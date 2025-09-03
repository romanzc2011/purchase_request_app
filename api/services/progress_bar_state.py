from dataclasses import dataclass, asdict
from enum import Enum, auto
from multiprocessing import shared_memory, Lock
from typing import List, Any
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

#-------------------------------------------------------------
# DOWNLOAD STEPS
#-------------------------------------------------------------
class DownloadStepName(Enum):
    FETCH_APPROVAL_DATA = auto()
    FETCH_FLAT_APPROVALS = auto()
    GET_JUSTIFICATIONS_AND_COMMENTS = auto()
    GET_CONTRACTING_OFFICER_BY_ID = auto()
    GET_LINE_ITEMS = auto()
    GET_SON_COMMENTS = auto()
    GET_ORDER_TYPES = auto()
    LOAD_PDF_TEMPLATE = auto()
    MERGE_DATA_INTO_TEMPLATE = auto()
    RENDER_PDF_BINARY = auto()
    SAVE_PDF_TO_DISK = auto()
    VERIFY_FILE_EXISTS = auto()
    
@dataclass
class DownloadStep:
    step_name: DownloadStepName
    weight: int
    done: bool = False
    download_state: bool = False
    
STEPS: List[DownloadStep] = [
    # DATABASE & DATA FETCHING
    DownloadStep(DownloadStepName.FETCH_APPROVAL_DATA,             10, False),  # Just a DB fetch (already very fast)
    DownloadStep(DownloadStepName.FETCH_FLAT_APPROVALS,            10, False),  # Related to above; medium-light work
    DownloadStep(DownloadStepName.GET_JUSTIFICATIONS_AND_COMMENTS,  5, False),  # Lightweight
    DownloadStep(DownloadStepName.GET_CONTRACTING_OFFICER_BY_ID,    5, False),  # simple lookup
    DownloadStep(DownloadStepName.GET_LINE_ITEMS,                  10, False),  # multiple rows
    DownloadStep(DownloadStepName.GET_SON_COMMENTS,                 5, False),  # Lightweight again
    DownloadStep(DownloadStepName.GET_ORDER_TYPES,                  5, False),  # Very quick small query

    # PDF PROCESSING
    DownloadStep(DownloadStepName.LOAD_PDF_TEMPLATE,                5, False),  # Style and assets load, small
    DownloadStep(DownloadStepName.MERGE_DATA_INTO_TEMPLATE,        15, False),  # This is a major content-binding step
    DownloadStep(DownloadStepName.RENDER_PDF_BINARY,               15, False),  # ReportLab rendering can be slow
    DownloadStep(DownloadStepName.SAVE_PDF_TO_DISK,                 5, False),  # Just file write
    DownloadStep(DownloadStepName.VERIFY_FILE_EXISTS,               5, False),  # Simple filesystem check
]

@dataclass
class ProgressState:
    id_generated:                bool = False
    pr_headers_inserted:         bool = False
    pdf_generated:               bool = False
    line_items_inserted:         bool = False
    generate_pdf:                bool = False
    send_approver_email:         bool = False
    send_requester_email:        bool = False
    email_sent_requester:        bool = False
    email_sent_approver:         bool = False
    pending_approval_inserted:   bool = False

from api.services.socketio_server.sio_instance import sio

class ProgressSharedMemory:
    
    def __init__(self, name="shm_progress_state"):
        self.STRUCT_FMT = '<' + '?' * 10
        self.STRUCT_SIZE = struct.calcsize(self.STRUCT_FMT)
        self.value: bool = False
        self._keep_bytes: bool = False
        self.total_steps: int = 10
        self.last_activity_time = time.time()
        self.cleanup_task = None

        try:
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.STRUCT_SIZE)
            logger.info(f"Shared memory initialized: {self.shm}")
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=name)
        self.name = name
        
        # Start cleanup task
        self.start_cleanup_task()
        
    def start_cleanup_task(self):
        """Start periodic cleanup of stale progress state"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
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
    def write(self, state: ProgressState):
        self.shm.buf[:self.STRUCT_SIZE] = self.to_bytes(state)
        
    #-------------------------------------------------------------
    # READ
    #-------------------------------------------------------------
    def read(self) -> ProgressState:
        packed_data = bytes(self.shm.buf[:self.STRUCT_SIZE])
        np_array = np.frombuffer(packed_data, dtype=np.uint8)
        return self.from_bytes(np_array)
        
    #-------------------------------------------------------------
    # UPDATE
    #-------------------------------------------------------------
    async def update(self, field: str, value: bool | int) -> None:
        current_state = self.read()
        
        self.value = value
        
        if hasattr(current_state, field):
            setattr(current_state, field, value)
            self.write(current_state)
            current_state = self.read()
            
            # Convert current_state to dict
            progress_dict = asdict(current_state) 
            percent = self.calc_progress_percentage()
            progress_dict["percent_complete"] = percent
            send_data = percent
            await sio.emit("progress_update", send_data, broadcast=True)
        else:
            logger.error(f"Field {field} does not exist")
            
    #-------------------------------------------------------------
    # CALC PROGRESS PERCENTAGE
    #-------------------------------------------------------------
    def calc_progress_percentage(self) -> float:
        current_state = self.read()
        step_count = sum(
            1 for field in vars(current_state).values()
            if isinstance(field, bool) and field
        )
        percent_complete = (step_count / self.total_steps) * 100
        return percent_complete
    
    #-------------------------------------------------------------
    # CALC PROGRESS DOWNLOAD
    #-------------------------------------------------------------
    def calc_download_progress(self, completed: list[DownloadStepName]) -> int:
        total_weight = sum(step.weight for step in STEPS)
        done_weight = sum(
			step.weight for step in STEPS if step.name in completed
		)
        return int((done_weight / total_weight) * 100)
    
    def on_steps_updated(self, completed: list[DownloadStepName]):
        percent = self.calc_download_progress(completed)
        logger.success(f"Percent: {percent}")
        
        # broadcast to front end
        asyncio.create_task(sio.emit("progress_update", {
			"event": "PROGRESS_UPDATE",
			"percent_complete": percent,
			"complete_steps": completed
		}, broadcast=True))

    #-------------------------------------------------------------
    # TO BYTES
    #-------------------------------------------------------------
    def to_bytes(self, state: ProgressState) -> bytes:
        return struct.pack(
            self.STRUCT_FMT,
            state.id_generated,
            state.pr_headers_inserted,
            state.pdf_generated,
            state.line_items_inserted,
            state.generate_pdf,
            state.send_approver_email,
            state.send_requester_email,
            state.email_sent_requester,
            state.email_sent_approver,
            state.pending_approval_inserted,
        )
        
    #-------------------------------------------------------------
    # FROM BYTES
    #-------------------------------------------------------------
    def from_bytes(self, b: bytes) -> ProgressState:
        if isinstance(b, np.ndarray):
            b = b.tobytes()
            
        unpacked = struct.unpack(self.STRUCT_FMT, b)
        return ProgressState(*unpacked)
    
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
        current_state = self.read()
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
        current_state = self.read()
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
