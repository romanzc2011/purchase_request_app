# ────────────────────────────────────────────────
# Pydantic Models
# ────────────────────────────────────────────────
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from api.schemas.enums import ItemStatus
import re

def to_snake_case(string: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()


class FileAttachment(BaseModel):
    attachment: Optional[bytes] = None
    name: Optional[str] = None
    type: Optional[str] = None
    size: Optional[int] = None

class PurchaseLineItem(BaseModel):
    uuid: Optional[str]
    purchase_request_uuid: Optional[str]
    item_description: str
    justification: str
    add_comments: Optional[str]
    train_not_aval: Optional[bool] = None
    needs_not_meet: Optional[bool] = None
    budget_obj_code: str
    fund: str
    quantity: int
    price_each: float
    total_price: float
    location: str
    status: ItemStatus
    created_time: Optional[datetime] = None

    class Config:
        alias_generator = to_snake_case
        populate_by_name = True

class PurchaseRequestSchema(BaseModel):
    uuid: Optional[str]
    id: str
    irq1_id: Optional[str]
    co: Optional[str]
    requester: str
    phoneext: int
    datereq: str
    dateneed: Optional[str]
    order_type: Optional[str]
    status: ItemStatus
    created_time: datetime
    line_items: List[PurchaseLineItem]

    class Config:
        alias_generator = to_snake_case
        populate_by_name = True
        from_attributes = True

class PurchaseResponse(BaseModel):
    message: str
    request_id: Optional[str]

class PurchaseRequestPayload(BaseModel):
    requester: str
    id: Optional[str] = None
    irq1_id: Optional[str] = None
    co: Optional[str] = None
    items: List[PurchaseLineItem]
    item_count: int

    class Config:
        alias_generator = to_snake_case
        populate_by_name = True

class PurchaseItem(BaseModel):
    uuid: Optional[str] = None
    id: Optional[str] = None
    irq1_id: Optional[str] = None
    requester: str
    phoneext: str
    datereq: str
    dateneed: Optional[str] = None
    order_type: Optional[str] = None
    file_attachments: Optional[List[dict]] = None
    item_description: str
    justification: str
    train_not_aval: Optional[bool] = None
    needs_not_meet: Optional[bool] = None
    budget_obj_code: str
    fund: str
    location: str
    price_each: float
    quantity: int
    total_price: Optional[float] = None
    status: Optional[str] = None

    class Config:
        alias_generator = to_snake_case
        populate_by_name = True
