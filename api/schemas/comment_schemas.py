from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

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

class CommentItem(BaseModel):
    uuid: str
    comment: str
    
class GroupCommentPayload(BaseModel):
    groupKey: str
    group_count: int
    item_desc: List[str]
    item_uuids: List[str]
    comment: List[CommentItem]