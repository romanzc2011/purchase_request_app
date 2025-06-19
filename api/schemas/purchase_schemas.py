# ────────────────────────────────────────────────
# Pydantic Models
# ────────────────────────────────────────────────
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from api.schemas.enums import ItemStatus
import re

def to_camel_case(string: str) -> str:
    parts = string.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


class FileAttachment(BaseModel):
    attachment: Optional[bytes] = None
    name: Optional[str] = None
    type: Optional[str] = None
    size: Optional[int] = None

class PurchaseLineItem(BaseModel):
    uuid: Optional[str] = Field(alias="UUID")
    id: Optional[str] = Field(alias="ID")
    irq1_id: Optional[str] = Field(alias="IRQ1_ID")
    purchase_request_uuid: Optional[str] = None
    requester: str
    phoneext: str
    datereq: str
    dateneed: Optional[str] = None
    order_type: Optional[str] = Field(alias="orderType")
    item_description: str = Field(alias="itemDescription")
    justification: str
    add_comments: Optional[str] = Field(alias="addComments", default=None)
    train_not_aval: Optional[bool] = Field(alias="trainNotAval", default=None)
    needs_not_meet: Optional[bool] = Field(alias="needsNotMeet", default=None)
    budget_obj_code: str = Field(alias="budgetObjCode")
    fund: str
    quantity: int
    price_each: float = Field(alias="priceEach")
    total_price: float = Field(alias="totalPrice")
    location: str
    status: str = Field(default="NEW REQUEST")
    file_attachments: Optional[List[dict]] = Field(alias="fileAttachments", default=None)
    is_cyber_sec_related: Optional[bool] = Field(alias="isCyberSecRelated", default=None)
    created_time: Optional[datetime] = Field(alias="createdTime", default=None)
    additional_comments: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class PurchaseRequestSchema(BaseModel):
    uuid: Optional[str] = Field(alias="UUID")
    id: str = Field(alias="ID")
    irq1_id: Optional[str] = Field(alias="IRQ1_ID")
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
        alias_generator = to_camel_case
        populate_by_name = True
        from_attributes = True

class PurchaseResponse(BaseModel):
    message: str
    request_id: Optional[str]

class PurchaseRequestPayload(BaseModel):
    requester: str
    id: Optional[str] = Field(alias="ID", default=None)
    irq1_id: Optional[str] = Field(alias="IRQ1_ID", default=None)
    co: Optional[str] = None
    items: List[PurchaseLineItem]
    item_count: int = Field(alias="itemCount")

    class Config:
        populate_by_name = True
        from_attributes = True

class PurchaseItem(BaseModel):
    uuid: Optional[str] = Field(alias="UUID", default=None)
    id: Optional[str] = Field(alias="ID", default=None)
    irq1_id: Optional[str] = Field(alias="IRQ1_ID", default=None)
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
    is_cyber_sec_related: Optional[bool] = None

    class Config:
        alias_generator = to_camel_case
        populate_by_name = True
        from_attributes = True
