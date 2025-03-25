from pydantic import BaseModel, ConfigDict
from typing import List, Optional

########################################################
## PYDANTIC SCHEMA -- structures data into pydantic, a style that easily converts to json with fastapi
########################################################

# purchase_request schema
class PurchaseRequestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    reqID: str
    requester: str
    recipient: str
    phoneext: int
    datereq: str
    dateneed: str
    orderType: str
    fileAttachments: bytes
    itemDescription: str
    justification: str
    addComments: Optional[str] = None
    trainNotAval: str
    needsNotMeet: str
    budgetObjCode: str
    fund: str
    priceEach: float
    totalPrice: float
    location: str
    quantity: int
    new_request: bool
    approved: bool


# approval schema
class AppovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    reqID: str
    requester: str
    recipient: str
    budgetObjCode: str
    fund: str
    quantity: int
    totalPrice: float
    priceEach: float
    location: str
    status: str
    new_request: str
    
    
    