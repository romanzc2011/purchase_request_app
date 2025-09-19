from dataclasses import dataclass, asdict
from enum import Enum, auto
from multiprocessing import shared_memory, Lock
from typing import List, Any
from api.utils.logging_utils import logger_init_ok
from loguru import logger
import struct
import asyncio
import numpy as np
import time

"""
This is to make progress data available globally. Just keeping up with work that 
needs to be complete and calculate what percentage has been completed. Structure
it neatly and send to frontend to display visually.

updating example
read_shm = shm_mgr.read()  # This reads the entire progress state struct
read_shm.total_steps = 10
shm_mgr.write(read_shm)

read_shm = shm_mgr.read()
read_shm.id_generated = True
logger.debug(f"READ SHM DATA TYPE: {type(read_shm.id_generated)}")
shm_mgr.write(read_shm)

read_shm = shm_mgr.read()
"""

@dataclass
class IPCState:
    request_pending: bool = False
    request_approved: bool = False
    approval_email_sent: bool = False

class IPCSharedMemory:
    
    def __init__(self, name="shm_progress_state"):
        self.STRUCT_FMT = '<' + '?' * 3  # Match IPCState fields: request_pending, request_approved, approval_email_sent
        self.STRUCT_SIZE = struct.calcsize(self.STRUCT_FMT)
        self.value: bool = False
        self._keep_bytes: bool = False
        self.total_steps: int = 10
        self.last_activity_time = time.time()
        self.cleanup_task = None

        try:
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.STRUCT_SIZE)
            logger_init_ok(f"Shared memory initialized: {self.shm}")
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=name)
        self.name = name
        
        # Don't start cleanup task during initialization - will be started in FastAPI startup
        
    def start_cleanup_task(self):
        """Start periodic cleanup of stale progress state"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
    def ensure_cleanup_task_started(self):
        """Ensure cleanup task is started (called from FastAPI startup)"""
        try:
            self.start_cleanup_task()
        except RuntimeError:
            # Event loop not running yet, will be called again from FastAPI startup
            pass
            
    async def _cleanup_loop(self):
        """Periodically check and clear stale progress state"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                current_time = time.time()
                
                # If no activity for 10 minutes, clear stale state
                if current_time - self.last_activity_time > 600:  # 10 minutes
                    logger.info("Clearing stale progress state due to inactivity")
                    await self.reset_progress_state()
                    
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
    
    @property
    def keep_bytes(self) -> bool:
        return self._keep_bytes
    
    @keep_bytes.setter
    def keep_bytes(self, value: bool):
        self._keep_bytes = value
        
    #-------------------------------------------------------------
    # WRITE
    #-------------------------------------------------------------
    def write(self, state: IPCState):
        self.shm.buf[:self.STRUCT_SIZE] = self.to_bytes(state)
        
    #-------------------------------------------------------------
    # READ
    #-------------------------------------------------------------
    async def read(self) -> IPCState:
        packed_data = bytes(self.shm.buf[:self.STRUCT_SIZE])
        np_array = np.frombuffer(packed_data, dtype=np.uint8)
        return self.from_bytes(np_array)
        
    #-------------------------------------------------------------
    # UPDATE
    #-------------------------------------------------------------
    async def update(self, field: str, value: bool | int) -> dict:
        current_state = await self.read()
        
        self.value = value
        
        if hasattr(current_state, field):
            setattr(current_state, field, value)
            self.write(current_state)
            current_state = await self.read()
            
            # Convert current_state to dict
            progress_dict = asdict(current_state)
            logger.debug(f"IPC DATA: {progress_dict}")
            
            return progress_dict
        else:
            logger.error(f"Field {field} does not exist")

    #-------------------------------------------------------------
    # TO BYTES
    #-------------------------------------------------------------
    def to_bytes(self, state: IPCState) -> bytes:
        return struct.pack(
            self.STRUCT_FMT,
            state.request_pending,
            state.request_approved,
            state.approval_email_sent,
        )
        
    #-------------------------------------------------------------
    # FROM BYTES
    #-------------------------------------------------------------
    def from_bytes(self, b: bytes) -> IPCState:
        if isinstance(b, np.ndarray):
            b = b.tobytes()
            
        unpacked = struct.unpack(self.STRUCT_FMT, b)
        return IPCState(*unpacked)
    
    #-------------------------------------------------------------
    # CLEAR STATE
    #-------------------------------------------------------------
    def clear_state(self):
        zero_bytes = bytes(self.STRUCT_SIZE)
        self.shm.buf[:self.STRUCT_SIZE] = zero_bytes
        
    #-------------------------------------------------------------
    # RESET PROGRESS STATE
    #-------------------------------------------------------------
    async def reset_progress_state(self):
        """Reset all progress flags to False"""
        current_state = await self.read()
        for field in vars(current_state):
            if isinstance(getattr(current_state, field), bool):
                setattr(current_state, field, False)
        self.write(current_state)
        logger.info("Progress state reset")
        
    #-------------------------------------------------------------
    # CHECK AND CLEAR STALE STATE
    #-------------------------------------------------------------
    async def check_and_clear_stale_state(self):
        """Check if progress state is stale and clear if needed"""
        current_state = await self.read()
        # If all flags are False, state is already clean
        if not any(vars(current_state).values()):
            return
            
        # Check if any progress was made but not completed
        # This could indicate a stale state
        logger.info("Checking for stale progress state...")
        await self.reset_progress_state()
        
    #-------------------------------------------------------------
    # CLOSE
    #-------------------------------------------------------------
    def close(self):
        self.shm.close()
    
    #-------------------------------------------------------------
    # UNLINK
    #-------------------------------------------------------------
    def unlink(self):
        self.shm.unlink()

# Create the global instance outside the class
ipc_status = IPCSharedMemory()
