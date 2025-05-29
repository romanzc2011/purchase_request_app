from typing import Tuple, List
from api.schemas.purchase_schemas import PurchaseRequestPayload
from api.schemas.email_schemas import LineItemsPayload, EmailPayload
from api.settings import settings

def build_email_payload(
    request: PurchaseRequestPayload,
) -> Tuple[List[LineItemsPayload], EmailPayload]:
    """
    Builds the email payload for the purchase request.
    """
    items = [
        LineItemsPayload(
            **item.dict(),
            link_to_request=settings.link_to_request
        )
        for item in request.items
    ]
    
    email = EmailPayload(
        subject         = f"Request Submitted - {request.ID}",
        sender          = "Purchase Request Approval System",
        to              = [request.requester],
        link_to_request = settings.link_to_request,
        items           = items
    )
    
    return items, email
        
