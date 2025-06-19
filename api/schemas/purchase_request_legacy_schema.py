from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from api.schemas.enums import ItemStatus

"""
This is to match the legacy purchase request schema. Refactored
the backend but still need to match the frontend.
"""

class PurchaseRequestLegacySchema(BaseModel):
    UUID: str
    ID: str
    requester: str
    phoneext: int
    datereq: str
    dateneed: Optional[str]
    orderType: Optional[str]
    fileAttachments: Optional[bytes]
    itemDescription: str
    justification: str
    addComments: Optional[str]
    trainNotAval: Optional[bool]
    needsNotMeet: Optional[bool]
    budgetObjCode: str
    fund: str
    status: ItemStatus
    priceEach: float
    totalPrice: float
    location: str
    quantity: int
    createdTime: datetime