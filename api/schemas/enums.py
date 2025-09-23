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
# ASSIGNED GROUPS
#-------------------------------------------------------------
class AssignedGroup(Enum):
    IT = "IT"
    FINANCE = "FINANCE"
    MANAGEMENT = "MANAGEMENT"
    DEPUTY_CLERK = "DEPUTY_CLERK"
    CHIEF_CLERK = "CHIEF_CLERK"
    
#-------------------------------------------------------------------------------------
# LDAP GROUP
#-------------------------------------------------------------------------------------
class LDAPGroup(Enum):
    IT_GROUP = "IT_GROUP"
    CUE_GROUP = "CUE_GROUP"
    ACCESS_GROUP = "ACCESS_GROUP"
    
#-------------------------------------------------------------------------------------
# CUE Clerk
#-------------------------------------------------------------------------------------
class CueClerk(Enum):
    DEPUTY_CLERK = "edmundbrown"
    CHIEF_CLERK = "edwardtakara"
    MANAGER = "lelarobichaux"
    TEST_USER = "romancampbell"
    
TEST_USER_ACTIVE = False

def is_test_user_active(username: str) -> bool:
    return username == CueClerk.TEST_USER.value and TEST_USER_ACTIVE

#-------------------------------------------------------------------------------------
# SOCKETIO EVENTS   (These are the events that are sent to the frontend)
#-------------------------------------------------------------------------------------
class SIOEvents(Enum):
    SEND_ORIGINAL_PRICE = "SEND_ORIGINAL_PRICE"
    MESSAGE_EVENT = "MESSAGE_EVENT"
    ERROR_EVENT = "ERROR_EVENT"
    START_TOAST = "START_TOAST"
    PROGRESS_UPDATE = "PROGRESS_UPDATE"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    NO_USER_FOUND = "NO_USER_FOUND"
    USER_FOUND = "USER_FOUND"
    SIGNAL_RESET = "SIGNAL_RESET"
    RESET_DATA = "RESET_DATA"
    PING_FROM_SERVER = "PING_FROM_SERVER"
