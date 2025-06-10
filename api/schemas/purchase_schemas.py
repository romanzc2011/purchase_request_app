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
    id:             str   = Field(..., alias="ID")
    uuid:           str   = Field(..., alias="UUID")
    irq1_id:        Optional[str] = Field(None, alias="IRQ1_ID")
    requester: str
    phoneext: str
    datereq: date
    dateneed: Optional[date] = None
    orderType: Optional[str] = None
    status: ItemStatus
    createdTime: Optional[datetime] = None
    
# --------------------------------------------------------------
#  PURCHASE REQUEST LINE ITEM SCHEMA
# --------------------------------------------------------------
class PurchaseRequestLineItem(BaseModel):
    id:             str   = Field(..., alias="ID")
    uuid:           str   = Field(..., alias="UUID")
    irq1_id:        Optional[str] = Field(None, alias="IRQ1_ID")
    requester:      str
    phoneext:       str
    datereq:        date
    dateneed:       Optional[date] = None
    order_type:     Optional[str]  = Field(None, alias="orderType")
    item_description: str         = Field(..., alias="itemDescription")
    justification:    str
    train_not_aval:   bool         = Field(..., alias="trainNotAval")
    needs_not_meet:   bool         = Field(..., alias="needsNotMeet")
    quantity:         int
    price:            float
    price_each:       float        = Field(..., alias="priceEach")
    total_price:      float        = Field(..., alias="totalPrice")
    fund:             str
    location:         str
    budget_obj_code:  str          = Field(..., alias="budgetObjCode")
    status:           ItemStatus
    file_attachments: Optional[List[FileAttachment]] = Field(None, alias="fileAttachments")
    
# --------------------------------------------------------------
#  PURCHASE REQUEST PAYLOAD SCHEMA
# --------------------------------------------------------------
class PurchaseRequestPayload(BaseModel):
    requester:      str
    items:          List[PurchaseRequestLineItem]
    itemCount:      int

# --------------------------------------------------------------
#  PURCHASE REQUEST RESPONSE SCHEMA
# --------------------------------------------------------------
class PurchaseResponse(BaseModel):
    message: str
    request_id: Optional[str]

    

