from dataclasses import dataclass
from enum import Enum, auto


class SubmitRequestStepName(Enum):
    # Initial Setup (10%)
    REQUEST_STARTED = auto()
    PAYLOAD_VALIDATED = auto()
    USER_AUTHENTICATED = auto()
    
    # Database Operations (25%)
    PURCHASE_REQUEST_ID_GENERATED = auto()
    PR_HEADER_UPDATED = auto()
    LINE_ITEMS_INSERTED = auto()
    FILES_UPLOADED = auto()
    CONTRACTING_OFFICER_RETRIEVED = auto()
    APPROVAL_RECORDS_CREATED = auto()
    PENDING_APPROVAL_INSERTED = auto()
    
    # PDF Generation (15%)
    PDF_GENERATION_STARTED = auto()
    PDF_TEMPLATE_LOADED = auto()
    PDF_DATA_MERGED = auto()
    PDF_RENDERED = auto()
    PDF_SAVED_TO_DISK = auto()
    
    # Email Notifications (20%)
    EMAIL_PAYLOAD_BUILT = auto()
    APPROVER_EMAIL_SENT = auto()
    REQUESTER_EMAIL_SENT = auto()
    
    # Finalization (10%)
    TRANSACTION_COMMITTED = auto()
    REQUEST_COMPLETED = auto()

@dataclass
class SubmitRequestStep:
    step_name: SubmitRequestStepName
    weight: int
    done: bool = False
    submit_request_process: bool = False

SUBMIT_REQUEST_STEPS = [
    SubmitRequestStep(SubmitRequestStepName.REQUEST_STARTED, 5),
    SubmitRequestStep(SubmitRequestStepName.PAYLOAD_VALIDATED, 5),
    SubmitRequestStep(SubmitRequestStepName.USER_AUTHENTICATED, 5),
    SubmitRequestStep(SubmitRequestStepName.PURCHASE_REQUEST_ID_GENERATED, 5),
    SubmitRequestStep(SubmitRequestStepName.PR_HEADER_UPDATED, 5),
    SubmitRequestStep(SubmitRequestStepName.LINE_ITEMS_INSERTED, 10),
    SubmitRequestStep(SubmitRequestStepName.FILES_UPLOADED, 5),
    SubmitRequestStep(SubmitRequestStepName.CONTRACTING_OFFICER_RETRIEVED, 5),
    SubmitRequestStep(SubmitRequestStepName.APPROVAL_RECORDS_CREATED, 5),
    SubmitRequestStep(SubmitRequestStepName.PENDING_APPROVAL_INSERTED, 5),
    SubmitRequestStep(SubmitRequestStepName.PDF_GENERATION_STARTED, 3),
    SubmitRequestStep(SubmitRequestStepName.PDF_TEMPLATE_LOADED, 3),
    SubmitRequestStep(SubmitRequestStepName.PDF_DATA_MERGED, 3),
    SubmitRequestStep(SubmitRequestStepName.PDF_RENDERED, 3),
    SubmitRequestStep(SubmitRequestStepName.PDF_SAVED_TO_DISK, 3),
    SubmitRequestStep(SubmitRequestStepName.EMAIL_PAYLOAD_BUILT, 5),
    SubmitRequestStep(SubmitRequestStepName.APPROVER_EMAIL_SENT, 5),
    SubmitRequestStep(SubmitRequestStepName.REQUESTER_EMAIL_SENT, 5),
    SubmitRequestStep(SubmitRequestStepName.TRANSACTION_COMMITTED, 9),
    SubmitRequestStep(SubmitRequestStepName.REQUEST_COMPLETED, 6),
]