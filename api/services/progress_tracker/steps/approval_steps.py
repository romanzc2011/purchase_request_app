from enum import Enum, auto
from dataclasses import dataclass
from typing import List
from loguru import logger

# -----------------------------------------------------------------------------
# APPROVAL STEPS
# -----------------------------------------------------------------------------
class ApprovalStepName(Enum):
    # Initial Setup
    APPROVAL_REQUEST_STARTED = auto()
    PAYLOAD_VALIDATED = auto()
    HANDLER_BASE_INITIALIZED = auto()
    
    # Chain Analysis
    CHAIN_STATUS_CHECKED = auto()
    ROUTER_CONFIGURED = auto()
    
    # Data Retrieval
    PENDING_APPROVAL_DATA_RETRIEVED = auto()
    APPROVAL_REQUEST_BUILT = auto()
    
    # IT Handler
    IT_HANDLER_INITIALIZED = auto()
    IT_APPROVAL_PROCESSED = auto()
    
    # Management Handler
    MANAGEMENT_HANDLER_INITIALIZED = auto()
    MANAGEMENT_APPROVAL_PROCESSED = auto()
    
    # Clerk Admin Handler
    CLERK_ADMIN_HANDLER_INITIALIZED = auto()
    CLERK_POLICY_CHECKED = auto()
    CLERK_APPROVAL_PROCESSED = auto()
    
    # Final Steps
    APPROVAL_UUID_RETRIEVED = auto()
    REQUEST_MARKED_APPROVED = auto()
    APPROVAL_EMAIL_SENT = auto()
    RESULT_OBJECT_BUILT = auto()
    FINAL_RESULTS_RETURNED = auto()

@dataclass
class ApprovalStep:
    step_name: ApprovalStepName
    weight: int
    done: bool = False
    approval_process: bool = False

APPROVAL_STEPS: List[ApprovalStep] = [
    # Initial Setup (10%)
    ApprovalStep(ApprovalStepName.APPROVAL_REQUEST_STARTED, 5),
    ApprovalStep(ApprovalStepName.PAYLOAD_VALIDATED, 5),
    ApprovalStep(ApprovalStepName.HANDLER_BASE_INITIALIZED, 0),
    
    # Chain Analysis (10%)
    ApprovalStep(ApprovalStepName.CHAIN_STATUS_CHECKED, 5),
    ApprovalStep(ApprovalStepName.ROUTER_CONFIGURED, 5),
    
    # Data Retrieval (15%)
    ApprovalStep(ApprovalStepName.PENDING_APPROVAL_DATA_RETRIEVED, 8),
    ApprovalStep(ApprovalStepName.APPROVAL_REQUEST_BUILT, 7),
    
    # IT Handler (15%)
    ApprovalStep(ApprovalStepName.IT_HANDLER_INITIALIZED, 7),
    ApprovalStep(ApprovalStepName.IT_APPROVAL_PROCESSED, 8),
    
    # Management Handler (20%)
    ApprovalStep(ApprovalStepName.MANAGEMENT_HANDLER_INITIALIZED, 10),
    ApprovalStep(ApprovalStepName.MANAGEMENT_APPROVAL_PROCESSED, 10),
    
    # Clerk Admin Handler (25%)
    ApprovalStep(ApprovalStepName.CLERK_ADMIN_HANDLER_INITIALIZED, 8),
    ApprovalStep(ApprovalStepName.CLERK_POLICY_CHECKED, 8),
    ApprovalStep(ApprovalStepName.CLERK_APPROVAL_PROCESSED, 9),
    
    # Final Steps (15%)
    ApprovalStep(ApprovalStepName.APPROVAL_UUID_RETRIEVED, 3),
    ApprovalStep(ApprovalStepName.REQUEST_MARKED_APPROVED, 3),
    ApprovalStep(ApprovalStepName.APPROVAL_EMAIL_SENT, 3),
    ApprovalStep(ApprovalStepName.RESULT_OBJECT_BUILT, 3),
    ApprovalStep(ApprovalStepName.FINAL_RESULTS_RETURNED, 3),
]

def get_approval_steps():
    return APPROVAL_STEPS