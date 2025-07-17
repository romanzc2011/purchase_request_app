from dataclasses import dataclass
from multiprocessing import shared_memory, Lock
from loguru import logger
import struct
import numpy as np
from api.services.websocket_manager import ConnectionManager

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

websock_connection = ConnectionManager()

# read_shm = shm_mgr.read()  # This reads the entire progress state struct
# read_shm.total_steps = 10
# shm_mgr.write(read_shm)
class ProgressSharedMemory:
    
    def __init__(self, name="shm_progress_state") -> None:
        self.STRUCT_FMT = '<' + '?' * 10 + 'i'
        self.STRUCT_SIZE = struct.calcsize(self.STRUCT_FMT)
        try:
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.STRUCT_SIZE)
            logger.info(f"Shared memory initialized: {self.shm}")
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=name)
        self.name = name
        
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
        logger.debug(f"NP ARRAY: {np_array} and is shape {np_array.shape}")
        return self.from_bytes(np_array)
        
    #-------------------------------------------------------------
    # UPDATE
    #-------------------------------------------------------------
    async def update(self, field: str, value: bool | int) -> None:
        current_state = self.read()
        if hasattr(current_state, field):
            setattr(current_state, field, value)
            self.write(current_state)
            self._add_total_steps(1)
            current_state = self.read()
            await websock_connection.broadcast(current_state)
            
            logger.debug(f"UPDATE COMPLETE: field-{field} value={value}")
        else:
            logger.error(f"Field {field} does not exist")
    
    #-------------------------------------------------------------
    # REDUCE TOTAL STEPS
    #-------------------------------------------------------------
    def _add_total_steps(self, step: int) -> None:
        current_state = self.read()
        if current_state.total_steps > 0:
            current_state.total_steps += step
            self.write(current_state)
        else:
            logger.error(f"Total steps is already 0")
                
    #-------------------------------------------------------------
    # CALC PROGRESS PERCENTAGE
    #-------------------------------------------------------------
    def calc_progress_percentage(self) -> float:
        current_state = self.read()
        percent_complete = (current_state.total_steps / current_state.total_steps) * 100
        logger.debug(f"PERCENT COMPLETE: {percent_complete}")
        return percent_complete
                
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
            state.total_steps
        )
    
    #-------------------------------------------------------------
    # FROM BYTES
    #-------------------------------------------------------------
    def from_bytes(self, b: bytes) -> ProgressState:
        unpacked = struct.unpack(self.STRUCT_FMT, b)
        return ProgressState(*unpacked)
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