from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum

# --------------------------------------------------------------
#  LINE ITEM STATUS ENUMERATION
# --------------------------------------------------------------
class ItemStatus(str, Enum):
    NEW_REQUEST = "NEW REQUEST"
    PENDING_APPROVAL = "PENDING APPROVAL"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ON_HOLD = "ON HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

# --------------------------------------------------------------
#  FILE ATTACHMENT SCHEMA
# --------------------------------------------------------------
class FileAttachment(BaseModel):
    attachment: Optional[bytes] = None
    name: Optional[str] = None
    type: Optional[str] = None
    size: Optional[int] = None
    
# --------------------------------------------------------------
#  PURCHASE REQUEST HEADER SCHEMA
# --------------------------------------------------------------
class PurchaseRequestHeader(BaseModel):
    id:             str
    uuid:           str 
    irq1_id:        Optional[str]
    requester: str
    phoneext: str
    datereq: date
    dateneed: Optional[date] = None
    order_type: Optional[str] = None
    status: ItemStatus
    created_time: Optional[datetime] = None
    
# --------------------------------------------------------------
#  PURCHASE REQUEST LINE ITEM SCHEMA
# --------------------------------------------------------------
class PurchaseRequestLineItem(BaseModel):
    id:             str
    uuid:           str
    irq1_id:        Optional[str]
    requester:      str
    phoneext:       str
    datereq:        date
    dateneed:       Optional[date] = None
    order_type:     Optional[str] = None
    item_description: str
    justification:    str
    train_not_aval:   bool
    needs_not_meet:   bool
    quantity:         int
    price:            float
    price_each:       float
    total_price:      float
    fund:             str
    location:         str
    budget_obj_code:  str
    status:           ItemStatus
    file_attachments: Optional[List[FileAttachment]]
    
# --------------------------------------------------------------
#  PURCHASE REQUEST PAYLOAD SCHEMA
# --------------------------------------------------------------
class PurchaseRequestPayload(BaseModel):
    requester:      str
    items:          List[PurchaseRequestLineItem]
    item_count:     int

# --------------------------------------------------------------
#  PURCHASE REQUEST RESPONSE SCHEMA
# --------------------------------------------------------------
class PurchaseResponse(BaseModel):
    message:    str
    request_id: Optional[str]

    

