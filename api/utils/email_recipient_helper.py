from api.services import smtp_service
from api.schemas.email_schemas import EmailPayloadRequest, LineItemsPayload
from api.schemas.ldap_schema import LDAPUser
from api.services.db_service import PurchaseRequestLineItem
from api.services import cache_service
from api import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import api.services.db_service as dbas
import asyncio

async def send_notification(
    db: AsyncSession,
    request: ApprovalRequest,
    current_user: LDAPUser,
) -> None:
    """
    Send notification to requester and approvers
    """
    #################################################################################
    ## BUILD EMAIL PAYLOADS
    #################################################################################
    # Query Approvals table for all data by uuid to make notification email
    stmt = select(dbas.Approval).where(dbas.Approval.UUID == approvals_uuid)
    result = await db.execute(stmt)
    approval_data = result.scalar_one_or_none()
    # Get additional comments
    additional_comments = cache_service.get_or_set(
        "comments",
        request.id,
        lambda: dbas.get_additional_comments_by_id(request.id)
    )
  
    for item in request.items:
        item.additional_comments = additional_comments
    
    items_for_email = [
        LineItemsPayload(
            budgetObjCode=item.budget_obj_code,
            itemDescription=item.item_description,
            location=item.location,
            justification=item.justification,
            quantity=item.quantity,
            priceEach=item.price_each,
            totalPrice=item.total_price,
            fund=item.fund
        )
        for item in request.items
    ]
    # --------------------------------------------------------
    # Send notification to final_approvers that they have a request to approve/deny
    email_request_payload = EmailPayloadRequest(
        model_type="email_request",
        ID=request.id,
        requester=request.requester,
        requester_email=request.requester_email,
        datereq=request.items[0].datereq,
        dateneed=request.items[0].dateneed,
        orderType=request.items[0].order_type,
        subject=f"Purchase Request #{request.id}",
        sender=settings.smtp_email_addr,
        to=None,   # Assign this in the smtp service
        cc=None,
        bcc=None,
        text_body=None,
        approval_link=f"{settings.link_to_request}",
        items=items_for_email,
        attachments=[pdf_path, *uploaded_files]
    )
    
    """
    # Make the to a condition, if this is a request from a requester, then we need to send it to the approvers
    # But we need to also send a confirmation to requester that is has been sent to the approvers
    """

    logger.info(f"EMAIL PAYLOAD REQUEST: {email_request_payload}")
    
    # Notify requester and approvers
    logger.info("Notifying requester and approvers")
    
    # Send request to approvers and requester
    async with asyncio.TaskGroup() as tg:
        tg.create_task(smtp_service.send_approver_email(email_request_payload))