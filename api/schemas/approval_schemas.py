from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from api.schemas.purchase_schemas import ItemStatus

# --------------------------------------------------------------
#  REQUEST APPROVAL PAYLOAD SCHEMAS
# --------------------------------------------------------------
class RequestPayload(BaseModel):
    ID: str
    item_count: int
    UUID: List[str] = Field(alias="item_uuids") # Renamed to UUID, expects "item_uuids" in JSON
    item_funds: List[str]
    totalPrice: List[float]
    target_status: List[ItemStatus] # Changed to use your ItemStatus enum for better validation
    action: str
    co: Optional[str] = None
    
class LineItemApprovalPayload(BaseModel):
    line_item_id: int
    target_status: ItemStatus
    comments: Optional[str] = None
    
class BulkApprovalPayload(BaseModel):
    approvals: List[LineItemApprovalPayload]

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
    datereq: str
    dateneed: Optional[str] = None
    orderType: Optional[str] = None
    budgetObjCode: str
    fund: str
    itemDescription: str
    justification: str
    addComments: Optional[List[str]] = None
    trainNotAval: Optional[bool] = False
    needsNotMeet: Optional[bool] = False
    quantity: int
    totalPrice: float
    priceEach: float
    location: str
    status: ItemStatus
    createdTime: datetime
    isCyberSecRelated: Optional[bool] = False

