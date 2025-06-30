# ────────────────────────────────────────────────
# Pydantic Models for Purchase Request API
# ────────────────────────────────────────────────
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from api.schemas.enums import ItemStatus
from api.utils.pydantic_utils import to_camel_case

# ────────────────────────────────────────────────
# FILE ATTACHMENT SCHEMA
# Used for file uploads in purchase requests
# ────────────────────────────────────────────────
class FileAttachment(BaseModel):
    attachment: Optional[bytes] = None
    name: Optional[str] = None
    type: Optional[str] = None
    size: Optional[int] = None

# ────────────────────────────────────────────────
# BASE PURCHASE ITEM SCHEMA
# Common fields shared between different purchase item representations
# ────────────────────────────────────────────────
class BasePurchaseItem(BaseModel):
    uuid: Optional[str] = Field(alias="UUID", default=None)
    id: Optional[str] = Field(alias="ID", default=None)
    irq1_id: Optional[str] = Field(alias="IRQ1_ID", default=None)
    co: Optional[str] = Field(alias="CO", default=None)
    requester: str
    phoneext: str
    datereq: str
    dateneed: Optional[str] = None
    order_type: Optional[str] = Field(alias="orderType", default=None)
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

    class Config:
        populate_by_name = True
        from_attributes = True

# ────────────────────────────────────────────────
# PURCHASE LINE ITEM SCHEMA
# Used for individual items within a purchase request
# Maps to PurchaseRequestLineItem ORM model
# ────────────────────────────────────────────────
class PurchaseLineItem(BasePurchaseItem):
    purchase_request_uuid: Optional[str] = None
    additional_comments: Optional[str] = None

# ────────────────────────────────────────────────
# API REQUEST/RESPONSE SCHEMAS
# ────────────────────────────────────────────────

# Used for incoming purchase request data from frontend
class PurchaseRequestPayload(BaseModel):
    requester: str
    id: Optional[str] = Field(alias="ID", default=None)
    irq1_id: Optional[str] = Field(alias="IRQ1_ID", default=None)
    co: Optional[str] = Field(alias="CO", default=None)
    items: List[PurchaseLineItem]
    item_count: int = Field(alias="itemCount")

    class Config:
        populate_by_name = True
        from_attributes = True

# Used for API responses after creating purchase requests
class PurchaseResponse(BaseModel):
    message: str
    request_id: Optional[str]

# ────────────────────────────────────────────────
# INDIVIDUAL ITEM SCHEMA (ALIAS FOR BACKWARD COMPATIBILITY)
# Used for processing individual purchase items
# Now inherits from BasePurchaseItem for consistency
# ────────────────────────────────────────────────
class PurchaseItem(BasePurchaseItem):
    # This is now just an alias for backward compatibility
    # All functionality is inherited from BasePurchaseItem
    pass

# ────────────────────────────────────────────────
# PDF SERVICE SCHEMA
# Used specifically for PDF generation service
# ────────────────────────────────────────────────
class PurchaseRequestHeader(BaseModel):
    uuid: str 
    irq1_id: Optional[str] = None
    co: Optional[str] = None
    requester: str
    phoneext: Optional[int] = None
    datereq: str
    dateneed: Optional[str] = None
    order_type: Optional[str] = None
    status: ItemStatus
    created_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
class AssignCOPayload(BaseModel):
    request_id: str
    contracting_officer_id: int
    contracting_officer: str