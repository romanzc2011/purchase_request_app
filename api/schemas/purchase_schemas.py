from pydantic import BaseModel, ConfigDict
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
    fileAttachments: Optional[List[bytes]] = None
    
# --------------------------------------------------------------
#  PURCHASE REQUEST PAYLOAD SCHEMA
# --------------------------------------------------------------
class PurchaseRequestPayload(BaseModel):
    requester: str
    items: List[PurchaseItem]
    IRQ1_ID: Optional[str] = None
    CO: Optional[str] = None
    fileAttachments: Optional[List[bytes]] = None
    itemCount: int
    

