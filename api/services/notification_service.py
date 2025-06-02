from typing import List
from api.schemas.comment_schemas import GroupCommentPayload
from api.schemas.email_schemas import EmailPayloadComment
from api.schemas.purchase_schemas import PurchaseRequestPayload
from api.dependencies.pras_dependencies import smtp_service
from api.dependencies.pras_dependencies import ldap_service
from api.services.smtp_service.builders import build_email_payload
from loguru import logger

#-------------------------------------------------------------------------------
# Notify requester
async def notify_requester(
    payload: PurchaseRequestPayload,
    generated_pdf_path: str,
    uploaded_files: List[str]
):
    """
    1) Build the “base” EmailPayload (subject, body template, line items, etc.)
    2) Look up the requester’s email address via LDAP
    3) Assign that address to `email_payload.to`
    4) Attach the generated PDF and any upload files
    5) Send the email via your async SMTP client
    """
    logger.info(f"PAYLOAD IN NOTIFY REQUESTER: {payload}")
    
    # Construct subject for email payload for requester
    subject = f"Purchase Request {payload.ID} for {payload.requester}"
    
    items, email_payload = build_email_payload(payload=payload, payload_type="request", subject=subject)
    logger.info(f"EMAIL PAYLOAD IN NOTIFY REQUESTER: {email_payload}")

    # Pull requester email from LDAP
    logger.info(f"Starting to lookup {payload.requester} email address")
    requester_email = await ldap_service.get_email_address(payload.requester)
    
    logger.info(f"Notifier has email address for {payload.requester}: {requester_email}")
    logger.info(f"email_payload: {email_payload}")
    
    email_payload.to = [requester_email]
    email_payload.attachments = [generated_pdf_path] + uploaded_files
    logger.info("About to send mail.....")
    
    # Send email
    await smtp_service.send_requester_email(email_payload)
    
#-------------------------------------------------------------------------------
# Notify approvers
async def notify_approvers(
    payload: PurchaseRequestPayload,
    generated_pdf_path: str,
    uploaded_files: List[str]
):
    """
    Notify the approvers of the purchase request.
    """
    # Build line items and base payload 
    #approvers = ldap_service.get_approvers_email("CUE-APPROVERS-GROUP")
    approvers = ["roman_campbell@lawb.uscourts.gov"]
    
    # Construct subject for email payload for approvers
    subject = f"Purchase Request {payload.ID} for {payload.requester}"
    
    # Build payload
    items, email_payload = build_email_payload(payload=payload, payload_type="request", subject=subject)
    logger.info(f"EMAIL PAYLOAD IN NOTIFY APPROVERS: {email_payload}")
    # Add approvers to payload
    email_payload.to = approvers
    email_payload.attachments = [generated_pdf_path] + uploaded_files
    
    # Send with approver template
    await smtp_service.send_approver_email(email_payload)