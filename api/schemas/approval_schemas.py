from api.schemas.comment_schemas import SonCommentSchema
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import date, datetime
from api.services.db_service import InboundStatus, ItemStatus

# ——————————————————————————————————————
# 2) A full “detail” view for internal use / metadata
# ——————————————————————————————————————

class LineItemApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    approver: str
    decision: ItemStatus
    comments: Optional[str]

# ——————————————————————————————————————
# 3) ApprovalDetailSchema
# for full detail (metadata + relationships)
# ——————————————————————————————————————
class ApprovalDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # all the table fields
    id: int
    uuid: str
    irq1_id: Optional[str]
    requester: str
    budget_obj_code: str
    fund: str
    location: str
    quantity: int
    price_each: float
    total_price: float
    item_description: str
    justification: str
    status: ItemStatus

    purchase_request_uuid: str
    purchase_request_id: str
    co: Optional[str]
    phoneext: int
    datereq: str
    dateneed: Optional[str]
    order_type: Optional[str]
    file_attachments: Optional[bytes]
    created_time: datetime
    is_cyber_sec_related: bool

    # relationships
    son_comments: Optional[List[SonCommentSchema]] = None
    line_item_approvals: Optional[List[LineItemApprovalSchema]] = None
    
# ——————————————————————————————————————
# APPROVAL CREATE SCHEMA
# what your endpoint expects in the request body
class ApprovalCreateSchema(BaseModel):
    """What the client must send to create a new Approval."""
    id: int
    uuid: str
    purchase_request_uuid: str
    purchase_request_id: str
    requester: str
    co: Optional[str] = None
    phoneext: int
    datereq: date
    dateneed: Optional[date] = None
    order_type: Optional[str] = None
    item_description: str
    justification: str
    train_not_aval: bool = Field(False, alias="train_not_aval")
    needs_not_meet: bool = Field(False, alias="needs_not_meet")
    budget_obj_code: str
    fund: str
    price_each: float
    total_price: float
    location: str
    quantity: int
    is_cyber_sec_related: bool = Field(False, alias="is_cyber_sec_related")
    status: ItemStatus
        
        # ——————————————————————————————————————
# 1) ApprovalTableSchema
# for listing in your table view (12 columns)
# ——————————————————————————————————————
class ApprovalTableSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    irq1_id: Optional[str] = Field(None, alias="irq1_id", title="IRQ1 #")
    requester: str
    budget_obj_code: str
    fund: str
    location: str
    quantity: int
    price_each: float
    total_price: float = Field(..., alias="Line Total")
    item_description: str
    justification: str
    status: ItemStatus

# ───────────────────────────────────────────────────────────────────────────────
# 1) INPUT / CREATE schemas (what your POST endpoints will expect)
# ───────────────────────────────────────────────────────────────────────────────
class ApprovalRequestCreate(BaseModel):
    approvals_uuid: str
    purchase_request_uuid: str
    action: ItemStatus
    target_status: ItemStatus
    co: Optional[str] = None
    item_funds: str
    total_price: float


# ───────────────────────────────────────────────────────────────────────────────
# 3) DETAIL schemas (single‐item endpoints with full relationships)
# ───────────────────────────────────────────────────────────────────────────────
class ApprovalRequestDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    approvals_uuid: str
    purchase_request_uuid: str
    action: ItemStatus
    target_status: ItemStatus
    co: Optional[str]
    item_funds: str
    total_price: float
    status: InboundStatus
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

class SonCommentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    approvals_uuid: str
    purchase_request_id: Optional[str]
    comment_text: Optional[str]
    son_requester: str
    item_description: Optional[str]
    created_at: datetime