from pydantic import BaseModel, Field, TypeAdapter
from typing import List, Optional
from typing import Annotated, Literal, Union
from datetime import date
from api.schemas.comment_schemas import GroupCommentPayload, CommentItem

# --------------------------------------------------------------
#  EMAIL LINE ITEMS PAYLOAD SCHEMAS
# --------------------------------------------------------------
class LineItemsPayload(BaseModel):
    itemDescription: str
    quantity: int
    priceEach: float
    totalPrice: float

# --------------------------------------------------------------
#  EMAIL PAYLOAD SCHEMAS - LineItemsPayload
# --------------------------------------------------------------
class EmailPayloadRequest(BaseModel):
    model_type: Literal["email_request"]
    ID: str
    requester: str
    datereq: date
    subject: str
    sender: str
    to: Optional[List[str]] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    text_body: Optional[str] = None
    approval_link: str
    items: List[LineItemsPayload]
    
class EmailPayloadComment(BaseModel):
    model_type: Literal["email_comments"]
    ID: str
    requester: str
    datereq: date
    subject: str
    sender: str
    to: List[str]
    approval_link: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    text_body: Optional[str] = None
    
    comment_data: List[GroupCommentPayload]
    
# Define discrimnated model
ValidModel = Annotated[
    Union[EmailPayloadRequest, EmailPayloadComment],
    Field(discriminator="model_type")]

_valid_model_adapter = TypeAdapter(ValidModel)