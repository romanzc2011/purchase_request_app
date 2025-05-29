

########################################################
##    APPROVAL SCHEMA
########################################################

    
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

