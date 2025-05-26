from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic import model_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

########################################################
## PYDANTIC SCHEMA -- structures data into pydantic, a style that 
# easily converts to json with fastapi, allows for sqlalchemy ORM
########################################################

########################################################    
##  TOKEN SCHEMA
########################################################
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username: str
    groups: List[str]
    
class LDAPUser(BaseModel):
    username: str
    email: EmailStr
    groups: List[str]

########################################################    
##  LINE ITEM STATUS ENUMERATION
########################################################
class ItemStatus(str, Enum):
    NEW_REQUEST = "NEW REQUEST"
    PENDING_APPROVAL = "PENDING APPROVAL"
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

from pydantic import BaseModel, Field
from typing  import List, Optional
from datetime import date

class FileAttachment(BaseModel):
    attachment: Optional[bytes] = None  # or Optional[str] if base64-encoded
    name:       Optional[str]
    type:       Optional[str]
    size:       Optional[int]

class LearnAndDev(BaseModel):
    trainNotAval: bool
    needsNotMeet: bool

class PurchaseItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    UUID:            str
    ID:              str
    IRQ1_ID:         Optional[str] = None
    requester:       str
    phoneext:        str
    datereq:         date
    dateneed:        Optional[date] = None
    orderType:       str
    fileAttachments: Optional[List[FileAttachment]] = None
    itemDescription: str
    justification:   str
    learnAndDev:     LearnAndDev
    quantity:        int     = Field(..., gt=0)
    price:           float   = Field(..., ge=0)
    priceEach:       float   = Field(..., ge=0.01)
    totalPrice:      float   = Field(..., ge=0)
    fund:            str
    location:        str
    budgetObjCode:   str     = Field(..., min_length=4, max_length=4)
    status:          ItemStatus  # Using the ItemStatus enum for validation

class PurchaseRequestPayload(BaseModel):
    requester: str
    items:     List[PurchaseItem]
    itemCount: int

class PurchaseResponse(BaseModel):
    message: str
    request_id: Optional[str]

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
## LINE ITEM STATUS SCHEMA
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
    UUID: List[str] = Field(alias="item_uuids") # Renamed to UUID, expects "item_uuids" in JSON
    item_funds: List[str]
    totalPrice: List[float]
    target_status: List[ItemStatus] # Changed to use your ItemStatus enum for better validation
    action: str
    co: Optional[str] = None

########################################################
##    APPROVE/DENY PAYLOAD SCHEMA ( RESPONSE )
########################################################
class ResponsePayload(BaseModel):
    status: str
    message: str
    
class IRQ1IDSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    IRQ1_ID: str
    
class CyberSecRelatedPayload(BaseModel):
    isCyberSecRelated: bool
    
########################################################
##    EMAIL PAYLOAD SCHEMA
########################################################
class EmailPayload(BaseModel):
    to: List[str]
    subject: str
    body: str
    file_attachments: Optional[List[str]] = None
    message: Optional[str] = None
    requester_name: Optional[str] = None
    approver_name: Optional[str] = None
    status: ItemStatus
    
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