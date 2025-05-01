from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

########################################################
## PYDANTIC SCHEMA -- structures data into pydantic, a style that easily converts to json with fastapi
########################################################
# pending_approval means the last person to approve request has not done so.
# For Approval: Matt: approves first -> Final approver
# purchase_request schema
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
    priceEach: float
    totalPrice: float
    location: str
    quantity: int
    newRequest: bool
    pendingApproval: bool
    approved: bool
    createdTime: datetime

# approval schema
class ApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ID: str
    IRQ1_ID: Optional[str] = None
    CO: Optional[str] = None
    requester: str
    budgetObjCode: str
    fund: str
    itemDescription: str
    justification: str
    addComments: Optional[str] = None
    trainNotAval: Optional[bool] = False
    needsNotMeet: Optional[bool] = False
    quantity: int
    totalPrice: float
    priceEach: float
    location: str
    status: str
    newRequest: bool
    pendingApproval: bool
    approved: bool
    createdTime: datetime
    approvedTime: Optional[datetime] = None 
    deniedTime: Optional[datetime] = None