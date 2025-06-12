from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from api.schemas.purchase_schemas import ItemStatus

# --------------------------------------------------------------
#  REQUEST APPROVAL PAYLOAD SCHEMAS
# --------------------------------------------------------------
class RequestPayload(BaseModel):
    id: str
    item_count: int
    uuid: List[str] = Field(alias="item_uuids") # Renamed to UUID, expects "item_uuids" in JSON
    item_funds: List[str]
    total_price: List[float]
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
    uuid: Optional[str] = None
    status: str
    last_updated: datetime
    updated_by: Optional[str] = None
    
class ApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    irq1_id: Optional[str] = None
    uuid: str
    co: Optional[str] = None
    requester: str
    datereq: str
    dateneed: Optional[str] = None
    order_type: Optional[str] = None
    budget_obj_code: str
    fund: str
    item_description: str
    justification: str
    add_comments: Optional[List[str]] = None
    train_not_aval: Optional[bool] = False
    needs_not_meet: Optional[bool] = False
    quantity: int
    total_price: float
    price_each: float
    location: str
    status: ItemStatus
    created_time: datetime
    is_cyber_sec_related: Optional[bool] = False

