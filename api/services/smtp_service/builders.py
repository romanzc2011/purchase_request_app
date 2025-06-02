from typing import Literal, Tuple, List, Union
from loguru import logger
from api.schemas.purchase_schemas import PurchaseRequestPayload
from api.schemas.email_schemas import LineItemsPayload, EmailPayloadRequest, EmailPayloadComment
from api.schemas.comment_schemas import GroupCommentPayload, CommentItem
from api.settings import settings

def build_email_payload(
    payload: PurchaseRequestPayload,
    payload_type: Literal["request", "comment"],
    comment_groups: List[GroupCommentPayload] = None,
    subject: str = None
) -> Union[EmailPayloadRequest, EmailPayloadComment]:
    """
    Build either:
      - EmailPayloadRequest (when payload_type == "request"), OR
      - EmailPayloadComment  (when payload_type == "comment")

    Args:
      request: PurchaseRequestPayload  (holds all the fields for a “request” email)
      payload_type: Literal["request","comment"]
      comment_groups: List[GroupCommentPayload] (only needed if payload_type=="comment")

    Returns:
      EmailPayloadRequest or EmailPayloadComment
    """
    logger.info(f"PAYLOAD IN BUILD EMAIL PAYLOAD: {payload}")
    
    # Common fields for both request and comment emails
    common_kwargs = {
        "ID": payload.ID,
        "requester": payload.requester,
        "datereq": payload.items[0].datereq,
        "subject": subject,
        "sender": settings.smtp_email_addr,
        "to": payload.to,                # List[str]
        "approval_link": payload.approval_link,
        "cc": payload.cc,
        "bcc": payload.bcc,
        "attachments": payload.attachments,
        "text_body": payload.text_body,
    }
    
    if payload_type == "request":
        # Build items list of LineItemsPayload
        items = [
            LineItemsPayload(
                **item.dict(),
                link_to_request=settings.link_to_request
            )
            for item in payload.items
        ]
    
        return EmailPayloadRequest(
            model_type      = "email_request",
            **common_kwargs,
            items=items
        )
        
    elif payload_type == "comment":
        if comment_groups is None:
            raise ValueError("comment_groups is required when payload_type == 'comment'")
        
        return EmailPayloadComment(
            model_type      = "email_comments",
            **common_kwargs,
            comment_data=comment_groups
        )
        
    else:       
        raise ValueError(f"Invalid payload_type: {payload_type}")
