from dataclasses import dataclass
from typing import Optional, List
from pydantic import BaseModel

class CommentItem(BaseModel):
    uuid: str
    comment: str
    
class GroupCommentPayload(BaseModel):
    groupKey: str
    group_count: int
    item_desc: List[str]
    item_uuids: List[str]
    comment: List[CommentItem]
    
@dataclass
class EmailMessage:
    subject: str
    sender: str
    to: List[str]
    link_to_request: str
    requester_name: Optional[str] = None
    approver_name: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None