import enum

class ItemStatus(enum.Enum):
    NEW = "NEW REQUEST"  # This matches what's in your database
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ON_HOLD = "ON HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    
class TaskStatus(enum.Enum):
    NEW         = "NEW"
    PENDING     = "PENDING"
    PROCESSED   = "PROCESSED"
    ERROR       = "ERROR"
    CANCELLED   = "CANCELLED" 