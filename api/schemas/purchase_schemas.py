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
#  INCOMING REQUEST DATA SCHEMA
# --------------------------------------------------------------
"""
This is what is incoming from front end, split up after validation
Must accept this model first
"""
class PurchaseRequestItem(BaseModel):
    uuid: str
    id: str
    requester: str
    phoneext: str
    datereq: date
    order_type: str
    item_description: str
    justification: str
    add_comments: Optional[List[str]] = None
    train_not_aval: Optional[bool] = False
    needs_not_meet: Optional[bool] = False
    quantity: int
    price_each: float
    total_price: float
    fund: str
    location: str
    budget_obj_code: str
    status: ItemStatus
    dateneed: Optional[date] = None
    file_attachments: Optional[List[FileAttachment]] = None
    created_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
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
    
    class Config:
        from_attributes = True
    
# --------------------------------------------------------------
#  PURCHASE REQUEST LINE ITEM SCHEMA
# --------------------------------------------------------------
class PurchaseRequestLineItem(BaseModel):
    id:                     int
    purchase_request_uuid:  str
    item_description:       str
    justification:          str
    add_comments:           Optional[str]
    train_not_aval:         bool
    needs_not_meet:         bool
    budget_obj_code:        str
    fund:                   str
    quantity:               int
    price_each:             float
    total_price:            float
    location:               str
    is_cyber_sec_related:   bool
    status:                 ItemStatus
    created_time:           datetime
    
    class Config:
        from_attributes = True
    
# --------------------------------------------------------------
#  PURCHASE REQUEST PAYLOAD SCHEMA
# --------------------------------------------------------------
class PurchaseRequestPayload(BaseModel):
    requester:      str
    items:  List[PurchaseRequestItem]
    item_count:     int

# --------------------------------------------------------------
#  PURCHASE REQUEST RESPONSE SCHEMA
# --------------------------------------------------------------
class PurchaseResponse(BaseModel):
    message:    str
    request_id: Optional[str]

    

