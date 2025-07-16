from dataclasses import dataclass
from multiprocessing import shared_memory
from loguru import logger
from ctypes import Structure, c_bool, c_int, sizeof, memmove, cast, POINTER, addressof, c_char
import struct


"""
This is to make progress data available globally. Just keeping up with work that 
needs to be complete and calculate what percentage has been completed. Structure
it neatly and send to frontend to display visually.
"""
@dataclass
class ProgressState:
    id_generated: bool = False
    pr_headers_inserted: bool = False
    pdf_generated: bool = False
    line_items_inserted: bool = False
    generate_pdf: bool = False
    send_approver_email: bool = False
    send_requester_email: bool = False
    email_sent_requester: bool = False
    email_sent_approver: bool = False
    pending_approval_inserted: bool = False
    total_steps: int = 10

# Define struct for 11 fields: 10 bools + 1 int
STRUCT_FMT = '<' + '?' * 10 + 'i'
STRUCT_SIZE = struct.calcsize(STRUCT_FMT)

def to_bytes(state: ProgressState) -> bytes:
    return struct.pack(
        STRUCT_FMT,
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
    
def from_bytes(b: bytes) -> ProgressState:
    unpacked = struct.unpack(STRUCT_FMT, b)
    return ProgressState(*unpacked)

class ProgressSharedMemory:
    def __init__(self, name="shm_progress_state") -> None:
        try:
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=STRUCT_SIZE)
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=name)
        self.name = name
        
    def write(self, state: ProgressState):
        self.shm.buf[:STRUCT_SIZE] = to_bytes(state)
        
    def read(self) -> ProgressState:
        return from_bytes(bytes(self.shm.buf[:STRUCT_SIZE]))
    
    def close(self):
        self.shm.close()
    
    def unlink(self):
        self.shm.unlin()