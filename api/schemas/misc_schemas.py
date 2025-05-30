from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from api.schemas.purchase_schemas import ItemStatus
    
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
##    MISCELLANEOUS SCHEMA
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

