from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from api.schemas.purchase_schemas import ItemStatus

# --------------------------------------------------------------
#  REQUEST APPROVAL PAYLOAD SCHEMAS
# --------------------------------------------------------------
class RequestPayload(BaseModel):
    item_uuids: List[str]
    target_status: List[ItemStatus]
    action: str
    co: Optional[str] = None

class ResponsePayload(BaseModel):
    status: str
    message: str

class LineItemStatusSchema(BaseModel):
    UUID: Optional[str] = None
    status: str
    last_updated: datetime
    updated_by: Optional[str] = None
    
class ApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    IRQ1_ID: Optional[str] = None
    UUID: str
    CO: Optional[str] = None
    requester: str
    dateneed: str
    datereq: str
    budgetObjCode: str
    fund: str
    itemDescription: str
    justification: str
    trainNotAval: Optional[bool] = False
    needsNotMeet: Optional[bool] = False
    quantity: int
    totalPrice: float
    priceEach: float
    location: str
    status: ItemStatus
    createdTime: datetime
    isCyberSecRelated: Optional[bool] = False
