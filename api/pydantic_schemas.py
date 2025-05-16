from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

########################################################
## PYDANTIC SCHEMA -- structures data into pydantic, a style that easily converts to json with fastapi
########################################################

########################################################    
##  LINE ITEM STATUS ENUMERATION
########################################################
class ItemStatus(str, Enum):
    NEW = "NEW REQUEST"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ON_HOLD = "ON HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

########################################################
##    PURCHASE REQUEST SCHEMA
########################################################
class PurchaseRequestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    requester: str
    phoneext: int
    datereq: str
    dateneed: str
    orderType: str
    fileAttachments: Optional[bytes] = None
    itemDescription: str
    justification: str
    addComments: Optional[str] = None
    trainNotAval: Optional[bool] = False
    needsNotMeet: Optional[bool] = False
    budgetObjCode: str
    fund: str
    status: ItemStatus
    priceEach: float
    totalPrice: float
    location: str
    quantity: int
    createdTime: datetime

########################################################
##    APPROVAL SCHEMA
########################################################
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
    
########################################################
##    LINE ITEM STATUS SCHEMA
########################################################
class LineItemStatusSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    UUID: Optional[str] = None
    status: str
    hold_until: Optional[datetime] = None
    last_updated: datetime
    updated_by: Optional[str] = None
    updater_username: Optional[str] = None
    updater_email: Optional[str] = None
    
########################################################
##    SON COMMENTS SCHEMA
########################################################
class SonCommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    UUID: Optional[str] = None
    comment_text: Optional[str] = None
    created_at: Optional[datetime] = None
    son_requester: str
    item_description: Optional[str] = None
    purchase_req_id: Optional[str] = None
  

########################################################
##    APPROVE/DENY PAYLOAD SCHEMA ( REQUEST )
########################################################  
class RequestPayload(BaseModel):
    ID: str
    UUID: str
    fund: str
    action: str

########################################################
##    APPROVE/DENY PAYLOAD SCHEMA ( RESPONSE )
########################################################
class ResponsePayload(BaseModel):
    status: str
    message: str
    
########################################################
##    REQUEST APPROVERS SCHEMA
# Current list: Ted, Edmund, Roman
# IN TESTING: Roman only
########################################################
class RequestApproversSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    email: EmailStr
    
########################################################
##    FINANCE DEPT MEMBERS SCHEMA
# Current list: Lauren Lee, Peter, Lela,Roman
# IN TESTING: Roman only
########################################################
class FinanceDeptMembersSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    email: EmailStr
    
class ITDeptMembersSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    email: EmailStr
    
class IRQ1IDSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    IRQ1_ID: str
    
class CyberSecRelatedPayload(BaseModel):
    isCyberSecRelated: bool
    
########################################################
##    COMMENT PAYLOAD SCHEMA
########################################################

class CommentItem(BaseModel):
    uuid: str
    comment: str
    
class GroupCommentPayload(BaseModel):
    groupKey: str
    group_count: int
    item_desc: List[str]
    item_uuids: List[str]
    comment: List[CommentItem]
    
    class Config:
        json_schema_extra = {
             "example": {
                "ID": "LAWB0001",
                "requester": "john.doe",
                "phoneext": 1234,
                "datereq": "2024-03-20",
                "dateneed": "2024-03-25",
                "orderType": "STANDARD",
                "itemDescription": "Office supplies",
                "justification": "Need for daily operations",
                "budgetObjCode": "12345",
                "fund": "GENERAL",
                "status": "NEW REQUEST",
                "priceEach": 29.99,
                "totalPrice": 299.90,
                "location": "Building A",
                "quantity": 10,
                "createdTime": "2024-03-20T10:00:00Z"
            }
        }