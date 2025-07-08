from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from api.schemas.purchase_schemas import ItemStatus
from api.utils.pydantic_utils import to_camel_case

# --------------------------------------------------------------
#  UPDATE PRICE EACH/ TOTAL PRICE PAYLOAD SCHEMAS
# --------------------------------------------------------------
class UpdatePricesPayload(BaseModel):
    purchase_request_id: str
    item_uuid: str
    new_price_each: float
    new_total_price: float
    status: ItemStatus

# --------------------------------------------------------------
#  REQUEST APPROVAL PAYLOAD SCHEMAS
# --------------------------------------------------------------
class RequestPayload(BaseModel):
    ID: str
    UUID: Optional[List[str]] = Field(alias="item_uuids") # Renamed to UUID, expects "item_uuids" in JSON
    item_funds: List[str]
    totalPrice: Optional[List[float]]
    target_status: List[ItemStatus] # Changed to use your ItemStatus enum for better validation
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

# --------------------------------------------------------------
#  APPROVAL REQUEST SCHEMA (for approval router)
# --------------------------------------------------------------
class ApprovalRequest(BaseModel):
    id: str
    uuid: str
    pending_approval_id: int
    fund: str
    status: ItemStatus
    total_price: float
    action: str
    approver: Optional[str] = None

class ApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    UUID: str
    purchase_request_id: str = Field(alias="ID")  # Map purchase_request_id to ID for backward compatibility
    IRQ1_ID: Optional[str] = None
    requester: str
    CO: Optional[str] = None
    phoneext: int
    datereq: str
    dateneed: Optional[str] = None
    orderType: Optional[str] = None
    fileAttachments: Optional[bytes] = None
    itemDescription: str
    justification: str
    trainNotAval: Optional[bool] = False
    needsNotMeet: Optional[bool] = False
    budgetObjCode: str
    fund: str
    priceEach: float
    totalPrice: float
    location: str
    quantity: int
    created_time: datetime = Field(alias="createdTime")  # Map created_time to createdTime for backward compatibility
    isCyberSecRelated: Optional[bool] = False
    status: ItemStatus

#------------------------------------------------
#  APPROVAL VIEW SCHEMAS
"""
This schema will be used as part of a backend API that will be used to
display the approval view. Because of the substantial backend refactoring
and database normalization, it is necessary to still meet the requirements
of the previous approval view. The way the approval flowed was great so
we will flatten the data we have into a single approval view that meets
the requirements of the previous approval view.
"""
#------------------------------------------------
class ApprovalView(BaseModel):
    # header fields
    id:                str
    uuid:              str
    irq1_id:           Optional[str]
    co:                Optional[str]
    requester:         str
    phoneext:          int
    datereq:           str
    dateneed:          Optional[str]
    order_type:        Optional[str]

    # line-item fields
    item_description:  str
    justification:     str
    add_comments:      Optional[str]
    train_not_aval:    bool
    needs_not_meet:    bool
    budget_obj_code:   str
    fund:              str

    # approval fields
    status:            str
    created_time:      datetime
    is_cyber_sec_related: bool = False

    # any other fields you were projecting
    price_each:        float
    total_price:       float
    location:          str
    quantity:          int

    class Config:
        alias_generator    = to_camel_case
        populate_by_name   = True
        by_alias           = True
        

# --------------------------------------------------------------
# FINAL APPROVAL Line Items Schema
class FinalApprovalLineItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    # Primary keys
    approvals_uuid: str
    line_item_uuid: str
    task_id: int
    
    # Approval fields
    approver: str
    status: ItemStatus
    created_at: datetime
    status: ItemStatus
    deputy_can_approve: bool  # total price must be equal to or less than $250
    

class DenyPayload(BaseModel):
    ID: str
    item_uuids: List[str]
    target_status: List[ItemStatus]  # Changed to List to match frontend
    action: str
    
    