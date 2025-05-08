from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from pydantic import Field
import enum
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
    IRQ1_ID: Optional[str] = None
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
    
########################################################
##    LINE ITEM STATUS SCHEMA
########################################################
class LineItemStatusSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    IRQ1_ID: Optional[str] = None
    status: str
    hold_until: Optional[datetime] = None
    last_updated: datetime
    updated_by: str
    
########################################################
##    SON COMMENTS SCHEMA
########################################################
class SonCommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    IRQ1_ID: Optional[str] = None
    comment_text: str
    created_at: datetime
    created_by: str
    son_requester: str

########################################################
##    COMMENT PAYLOAD SCHEMA
########################################################
class CommentPayload(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)

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