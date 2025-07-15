from dataclasses import dataclass, asdict
import json
from loguru import logger
from api.services.redis_client import r

"""
This is to make progress data available globally. Just keeping up with work that 
needs to be complete and calculate what percentage has been completed. Structure
it neatly and send to frontend to display visually.
"""
@dataclass
class ProgressBarSteps:
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
    
class ProgressBar:
    def __init__(self) -> None:
        self.progress_steps = ProgressBarSteps()
        
    #-----------------------------------------------------------------------------------
	# SETTERS
 	#-----------------------------------------------------------------------------------
    def set_id_generated(self, id_generated: bool):
        self.progress_steps.id_generated = id_generated
        
    def set_pr_headers_inserted(self, pr_headers_inserted: bool):
        self.progress_steps.pr_headers_inserted = pr_headers_inserted
        
    def set_pdf_generated(self,pdf_generated: bool) -> None:
        self.progress_steps.pdf_generated = pdf_generated
        
    def set_line_items_inserted(self,line_items_inserted: bool) -> None:
        self.progress_steps.line_items_inserted = line_items_inserted
        
    def set_generate_pdf(self, generate_pdf: bool) -> None:
        self.progress_steps.generate_pdf = generate_pdf
        
    def set_send_approver_email(self, send_approver_email: bool) -> None:
        self.progress_steps.send_approver_email = send_approver_email
        
    def set_send_requester_email(self, send_requester_email: bool) -> None:
        self.progress_steps.send_requester_email = send_requester_email
        
    def set_email_sent_requester(self, email_sent_requester: bool) -> None:
        self.progress_steps.email_sent_requester = email_sent_requester
        
    def set_email_sent_approver(self, email_sent_approver: bool) -> None:
        self.progress_steps.email_sent_approver = email_sent_approver
        
    def set_pending_approval_inserted(self, pending_approval_inserted: bool) -> None:
        self.progress_steps.pending_approval_inserted = pending_approval_inserted
        
    #-----------------------------------------------------------------------------------
	# GETTERS
 	#-----------------------------------------------------------------------------------
    def get_id_generated(self) -> bool:
        return self.progress_steps.id_generated
    
    def get_pdf_generated(self) -> bool:
        return self.progress_steps.pdf_generated
    
    def get_line_items_inserted(self) -> bool:
        return self.progress_steps.line_items_inserted
    
    def get_generate_pdf(self) -> bool:
        return self.progress_steps.generate_pdf
    
    def get_send_approver_email(self) -> bool:
        return self.progress_steps.send_approver_email
    
    def get_send_requester_email(self) -> bool:
        return self.progress_steps.send_requester_email
    
    def get_email_sent_requester(self) -> bool:
        return self.progress_steps.email_sent_requester
    
    def get_email_sent_approver(self) -> bool:
        return self.progress_steps.email_sent_approver
    
    def get_pending_approval_inserted(self) -> bool:
        return self.progress_steps.pending_approval_inserted
    
    def get_progress_steps(self) -> ProgressBarSteps:
        return self.progress_steps
    
    # Caculate the current percentage of request submission complete
    def get_progress_percentage(self) -> float:
        completed = 0
        for key, value in vars(self.progress_steps).items():
            if isinstance(value, bool) and value:
                completed += 1
        return (completed / self.progress_steps.total_steps) * 100