from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# --------------------------------------------------------------
#  EMAIL LINE ITEMS PAYLOAD SCHEMAS
# --------------------------------------------------------------
class LineItemsPayload(BaseModel):
    itemDescription: str
    quantity: int
    priceEach: float
    totalPrice: float

# --------------------------------------------------------------
#  EMAIL PAYLOAD SCHEMAS
# --------------------------------------------------------------
class EmailPayload(BaseModel):
    ID: str
    requester: str
    datereq: date
    subject: str
    sender: str
    to: List[str]
    approval_link: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    comments: Optional[str] = None
    text_body: Optional[str] = None
    
    items: List[LineItemsPayload]