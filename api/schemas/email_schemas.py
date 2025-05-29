from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# --------------------------------------------------------------
#  EMAIL LINE ITEMS PAYLOAD SCHEMAS
# --------------------------------------------------------------
class LineItemsPayload(BaseModel):
    ID: str
    requester: str
    datereq: date
    itemDescription: str
    quantity: int
    priceEach: float
    totalPrice: float
    link_to_request: Optional[str] = None

# --------------------------------------------------------------
#  EMAIL PAYLOAD SCHEMAS
# --------------------------------------------------------------
class EmailPayload(BaseModel):
    subject: str
    sender: str
    to: List[str]
    link_to_request: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    items: List[LineItemsPayload]