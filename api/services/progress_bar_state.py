from dataclasses import dataclass
from multiprocessing import shared_memory
from loguru import logger
from ctypes import Structure, c_bool, c_int, sizeof, memmove
import ctypes


"""
This is to make progress data available globally. Just keeping up with work that 
needs to be complete and calculate what percentage has been completed. Structure
it neatly and send to frontend to display visually.
"""
class ProgressState(Structure):
    _fields_ = [
        ("id_generated", c_bool),
        ("pr_headers_inserted", c_bool),
        ("pdf_generated", c_bool),
        ("line_items_inserted", c_bool),
        ("generate_pdf", c_bool),
        ("send_approver_email", c_bool),
        ("send_requester_email", c_bool),
        ("email_sent_requester", c_bool),
        ("email_sent_approver", c_bool),
        ("pending_approval_inserted", c_bool),
        ("total_steps", c_int)
    ]

class ProgressBar:
    def __init__(self) -> None:
        self.progress_state = ProgressState()
        
    #-----------------------------------------------------------------------------------
	# SETTERS
 	#-----------------------------------------------------------------------------------
    def set_id_generated(self, id_generated: bool):
        self.progress_state.id_generated = id_generated
        
    def set_pr_headers_inserted(self, pr_headers_inserted: bool):
        self.progress_state.pr_headers_inserted = pr_headers_inserted
        
    def set_pdf_generated(self,pdf_generated: bool) -> None:
        self.progress_state.pdf_generated = pdf_generated
        
    def set_line_items_inserted(self,line_items_inserted: bool) -> None:
        self.progress_state.line_items_inserted = line_items_inserted
        
    def set_generate_pdf(self, generate_pdf: bool) -> None:
        self.progress_state.generate_pdf = generate_pdf
        
    def set_send_approver_email(self, send_approver_email: bool) -> None:
        self.progress_state.send_approver_email = send_approver_email
        
    def set_send_requester_email(self, send_requester_email: bool) -> None:
        self.progress_state.send_requester_email = send_requester_email
        
    def set_email_sent_requester(self, email_sent_requester: bool) -> None:
        self.progress_state.email_sent_requester = email_sent_requester
        
    def set_email_sent_approver(self, email_sent_approver: bool) -> None:
        self.progress_state.email_sent_approver = email_sent_approver
        
    def set_pending_approval_inserted(self, pending_approval_inserted: bool) -> None:
        self.progress_state.pending_approval_inserted = pending_approval_inserted
        
    #-----------------------------------------------------------------------------------
	# GETTERS
 	#-----------------------------------------------------------------------------------
    def get_id_generated(self) -> bool:
        return self.progress_state.id_generated
    
    def get_pdf_generated(self) -> bool:
        return self.progress_state.pdf_generated
    
    def get_line_items_inserted(self) -> bool:
        return self.progress_state.line_items_inserted
    
    def get_generate_pdf(self) -> bool:
        return self.progress_state.generate_pdf
    
    def get_send_approver_email(self) -> bool:
        return self.progress_state.send_approver_email
    
    def get_send_requester_email(self) -> bool:
        return self.progress_state.send_requester_email
    
    def get_email_sent_requester(self) -> bool:
        return self.progress_state.email_sent_requester
    
    def get_email_sent_approver(self) -> bool:
        return self.progress_state.email_sent_approver
    
    def get_pending_approval_inserted(self) -> bool:
        return self.progress_state.pending_approval_inserted
    
    def get_progress_state(self) -> ProgressState:
        return self.progress_state
    
    # Caculate the current percentage of request submission complete
    def get_progress_percentage(self) -> float:
        completed = 0
        for key, value in vars(self.progress_state).items():
            if isinstance(value, bool) and value:
                completed += 1
        return (completed / self.progress_state.total_steps) * 100
    
    def read_progress_state() -> ProgressState:
        # connect to shm
        existing_shm = shared_memory.SharedMemory(name="shm_progress_state")
        buffer = existing_shm.buf
        state = ProgressState.from_buffer(buffer)
        return state
        
        
try:
	progress_state = ProgressState()    
	size = sizeof(ProgressState)
	shm = shared_memory.SharedMemory(create=True, size=size, name="shm_progress_state")
	buffer = shm.buf
	ctypes.memmove(buffer, ctypes.addressof(progress_state), size)
except FileExistsError:
    shm = shared_memory.SharedMemory(name="shm_progress_state", create=False)