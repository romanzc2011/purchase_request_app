from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

########################################################
##    SON COMMENTS SCHEMA
########################################################
class SonCommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    approvals_uuid: Optional[str] = None
    purchase_request_id: Optional[str] = None
    comment_text: Optional[str] = None
    created_at: Optional[datetime] = None
    son_requester: str
    item_description: Optional[str] = None

class CommentItem(BaseModel):
    uuid: str
    comment: str
    
class GroupCommentPayload(BaseModel):
    group_key: str
    group_count: int
    item_desc: List[str]
    item_uuids: List[str]
    comment: List[CommentItem]