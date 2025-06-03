from pydantic import BaseModel
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
#  PURCHASE ITEM SCHEMA
# --------------------------------------------------------------
class PurchaseItem(BaseModel):
    UUID: str
    ID: str
    requester: str
    phoneext: str
    datereq: date
    orderType: str
    itemDescription: str
    justification: str
    trainNotAval: Optional[bool] = False
    needsNotMeet: Optional[bool] = False
    quantity: int
    price: float
    priceEach: float
    totalPrice: float
    fund: str
    location: str
    budgetObjCode: str
    status: ItemStatus
    dateneed: Optional[date] = None
    fileAttachments: Optional[List[FileAttachment]] = None
    createdTime: Optional[datetime] = None
    
    
# --------------------------------------------------------------
#  PURCHASE REQUEST PAYLOAD SCHEMA
# --------------------------------------------------------------
class PurchaseRequestPayload(BaseModel):
    requester: str
    ID: Optional[str] = None
    IRQ1_ID: Optional[str] = None
    CO: Optional[str] = None
    items: List[PurchaseItem]
    fileAttachments: Optional[List[bytes]] = None
    itemCount: int
    
class PurchaseResponse(BaseModel):
    message: str
    request_id: Optional[str]
    

