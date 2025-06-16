from pydantic import BaseModel, Field, TypeAdapter
from typing import List, Optional
from typing import Annotated, Literal, Union
from datetime import date
from api.schemas.comment_schemas import GroupCommentPayload, CommentItem

# --------------------------------------------------------------
#  EMAIL LINE ITEMS PAYLOAD SCHEMAS
# --------------------------------------------------------------
class LineItemsPayload(BaseModel):
    budget_obj_code: str
    item_description: str
    location: str
    justification: str
    quantity: int
    price_each: float
    total_price: float
    fund: str

# --------------------------------------------------------------
#  EMAIL PAYLOAD SCHEMAS - EmailPayloadRequest
# --------------------------------------------------------------
class EmailPayloadRequest(BaseModel):
    model_type: Literal["email_request"]
    request_id: str
    requester: str
    requester_email: str
    datereq: date
    dateneed: Optional[date] = None
    order_type: Optional[str] = None 
    subject: str
    sender: str
    to: Optional[List[str]] = None  # TODO: This will be the approvers in prod
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    text_body: Optional[str] = None
    approval_link: str
    items: List[LineItemsPayload]
    
# --------------------------------------------------------------
#  EMAIL PAYLOAD SCHEMAS - EmailPayloadComment
# --------------------------------------------------------------    
class EmailPayloadComment(BaseModel):
    model_type: Literal["email_comments"]
    id: str
    requester: str
    requester_email: str
    datereq: date
    subject: str
    sender: str
    to: Optional[List[str]] = None  # TODO: This will be the approvers in prod
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    text_body: Optional[str] = None
    
    comment_data: List[GroupCommentPayload]
    
# Define discrimnated model
ValidModel = Annotated[
    Union[EmailPayloadRequest, EmailPayloadComment],
    Field(discriminator="model_type")]

_valid_model_adapter = TypeAdapter(ValidModel)