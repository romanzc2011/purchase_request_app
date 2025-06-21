import enum

class ItemStatus(enum.Enum):
    NEW_REQUEST = "NEW REQUEST"  # This matches what's in your database
    PENDING_APPROVAL = "PENDING APPROVAL"  # Added to match frontend expectations
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ON_HOLD = "ON HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class TaskStatus(enum.Enum):
    NEW_REQUEST = "NEW REQUEST"
    PENDING     = "PENDING"
    PROCESSED   = "PROCESSED"
    ERROR       = "ERROR"
    CANCELLED   = "CANCELLED" 