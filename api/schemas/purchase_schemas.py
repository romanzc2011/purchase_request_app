from pydantic import BaseModel, model_validator
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
    ID: str
    UUID: str
    IRQ1_ID: Optional[str] = None
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
    ID:                     str
    UUID:                   str
    purchase_req_id:        str
    itemDescription:        str
    justification:          str
    additional_comments:    Optional[List[str]] = None
    trainNotAval:           Optional[bool] = False
    needsNotMeet:           Optional[bool] = False
    quantity:                int
    priceEach:              float
    totalPrice:             float
    fund:                   str
    location:               str
    budgetObjCode:          str
    status:                 ItemStatus
    createdTime:            Optional[datetime] = None
    fileAttachments: Optional[List[FileAttachment]] = None
    
# --------------------------------------------------------------
#  PURCHASE REQUEST PAYLOAD SCHEMA
# --------------------------------------------------------------
class PurchaseRequestPayload(BaseModel):
    header: PurchaseRequestHeader
    items: List[PurchaseRequestLineItem]
    
    @model_validator(mode="after")
    def _propagate_header_to_items(self, data):
        hdr, items = data.header, data.items
        for item in items:
            item.ID = hdr.ID
            item.UUID = hdr.UUID
            item.purchase_req_id = hdr.ID
        return data
            

# --------------------------------------------------------------
#  PURCHASE REQUEST RESPONSE SCHEMA
# --------------------------------------------------------------
class PurchaseResponse(BaseModel):
    message: str
    request_id: Optional[str]

    

