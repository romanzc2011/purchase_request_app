from dataclasses import dataclass
from multiprocessing import shared_memory, Lock
from loguru import logger
import struct
import numpy as np
import os
import mmap
import tempfile

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
class ProgressState:
    id_generated: 				bool = False
    pr_headers_inserted: 		bool = False
    pdf_generated: 				bool = False
    line_items_inserted: 		bool = False
    generate_pdf: 				bool = False
    send_approver_email: 		bool = False
    send_requester_email: 		bool = False
    email_sent_requester: 		bool = False
    email_sent_approver: 		bool = False
    pending_approval_inserted: 	bool = False
    total_steps: int = 10



class ProgressSharedMemory:
    _lock = Lock()
    
    def __init__(self, name="shm_progress_state") -> None:
        self.STRUCT_FMT = '<' + '?' * 10 + 'i'
        self.STRUCT_SIZE = struct.calcsize(self.STRUCT_FMT)
        try:
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.STRUCT_SIZE)
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=name)
        self.name = name
        
    # WRITE
    def write(self, state: ProgressState):
        with self._lock:
            self.shm.buf[:self.STRUCT_SIZE] = self.to_bytes(state)
        
    # READ
    def read(self) -> ProgressState:
        with self._lock:
            packed_data = bytes(self.shm.buf[:self.STRUCT_SIZE])
            np_array = np.frombuffer(packed_data, dtype=np.uint8)
            logger.debug(f"NP ARRAY: {np_array} and is shape {np_array.shape}")
            return self.from_bytes(np_array)
        
    def update(self, field: str, value: bool | int) -> None:
        with self._lock:
            current_state = self.read()
            if hasattr(current_state, field):
                setattr(current_state, field, value)
                self.write(current_state)
            else:
                logger.error(f"Field {field} does not exist")
                
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
            state.total_steps
        )
    def from_bytes(self, b: bytes) -> ProgressState:
        unpacked = struct.unpack(self.STRUCT_FMT, b)
        return ProgressState(*unpacked)
    
    
    
    
    
    
    def close(self):
        self.shm.close()
    
    def unlink(self):
        self.shm.unlink()