from enum import Enum

#-------------------------------------------------------------
# ITEM STATUS
#-------------------------------------------------------------
class ItemStatus(Enum):
    NEW_REQUEST = "NEW REQUEST"  # This matches what's in your database
    PENDING_APPROVAL = "PENDING APPROVAL"  # Added to match frontend expectations
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ON_HOLD = "ON HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

#-------------------------------------------------------------
# TASK STATUS
#-------------------------------------------------------------
class TaskStatus(Enum):
    NEW_REQUEST = "NEW REQUEST"
    PENDING     = "PENDING"
    PROCESSED   = "PROCESSED"
    ERROR       = "ERROR"
    CANCELLED   = "CANCELLED" 

#-------------------------------------------------------------
# DOWNLOAD STEPS
#-------------------------------------------------------------
class DownloadStepName(str, Enum):
    FETCH_APPROVAL_DATA = "fetch_approval_data"
    FETCH_FLAT_APPROVALS = "fetch_flat_approvals"
    GET_JUSTIFICATIONS_AND_COMMENTS = "get_justifications_and_comments"
    GET_CONTRACTING_OFFICER_BY_ID = "get_contracting_officer_by_id"
    GET_LINE_ITEMS = "get_line_items"
    GET_SON_COMMENTS = "get_son_comments"
    GET_ORDER_TYPES = "get_order_types"
    LOAD_PDF_TEMPLATE = "load_pdf_template"
    MERGE_DATA_INTO_TEMPLATE = "merge_data_into_template"
    RENDER_PDF_BINARY = "render_pdf_binary"
    SAVE_PDF_TO_DISK = "save_pdf_to_disk"
    VERIFY_FILE_EXISTS = "verify_file_exists"
