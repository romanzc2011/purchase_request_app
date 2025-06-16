from api.schemas.comment_schemas import SonCommentSchema
from api.schemas.purchase_schemas import PurchaseRequestHeader
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import date, datetime
from api.services.db_service import TaskStatus, ItemStatus

# ——————————————————————————————————————
# 2) A full "detail" view for internal use / metadata
# ——————————————————————————————————————

class LineItemApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_id: str
    approver: str
    decision: ItemStatus
    comments: Optional[str]

# ——————————————————————————————————————
# 3) ApprovalDetailSchema
# for full detail (metadata + relationships)
# ——————————————————————————————————————
class ApprovalDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # core approval fields
    id: int
    uuid: str
    purchase_request_uuid: str
    purchase_request_id: str
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

    # parent‐request fields
    purchase_request_uuid: str
    purchase_request_id: str
    co: Optional[str]
    phoneext: int
    datereq: date
    dateneed: Optional[date]
    order_type: Optional[str]
    file_attachments: Optional[bytes]
    created_time: datetime
    is_cyber_sec_related: bool

    # nested relationships
    son_comments: Optional[List[SonCommentSchema]] = None
    line_item_approvals: Optional[List[LineItemApprovalSchema]] = None
    purchase_request: Optional[PurchaseRequestHeader] = None
    
# ——————————————————————————————————————
# APPROVAL CREATE SCHEMA
# what your endpoint e`xpects in the request body
class ApprovalSchema(BaseModel):
    """What the client must send to create a new Approval."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    purchase_request_uuid: str
    irq1_id: Optional[str] = None
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
    created_time: datetime

    @property
    def request_id(self) -> str:
        return self.purchase_request.request_id if hasattr(self, 'purchase_request') else None

    @property
    def purchase_request_id(self) -> str:
        return self.purchase_request.request_id if hasattr(self, 'purchase_request') else None

# ——————————————————————————————————————
# 1) ApprovalTableSchema
# for listing in your table view (12 columns)
# ——————————————————————————————————————
class ApprovalTableSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    purchase_request_uuid: str
    purchase_request_id: str
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
class PendingApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    request_id: str
    purchase_request_uuid: str
    purchase_request_line_item_id: Optional[int] = None
    assigned_group: str

    # lifecycle of the task
    status: TaskStatus
    # what the approver chose
    action: Optional[ItemStatus] = None

    # timestamps & errors
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SonCommentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    approvals_uuid: str
    request_id: Optional[str]
    comment_text: Optional[str]
    son_requester: str
    item_description: Optional[str]
    created_at: datetime