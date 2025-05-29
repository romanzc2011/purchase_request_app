from typing import List
from api.schemas.purchase_schemas import PurchaseRequestPayload
from api.services.smtp_service.smtp_service import SMTP_Service
from api.services.smtp_service.builders import build_email_payload
from pras_api import smtp_service, ldap_service, settings

#-------------------------------------------------------------------------------
# Notify requester
async def notify_requester(
    request: PurchaseRequestPayload,
    generated_pdf_path: str,
    uploaded_files: List[str]
):
    """
    Notify the requester of the purchase request.
    """
    # Build line items and base payload
    items, email_payload = build_email_payload(request)

    # Pull requester email from LDAP
    requester_email = ldap_service.get_email_address(
        ldap_service.get_connection(),
        request.requester
    )
    email_payload.to = [requester_email]
    email_payload.attachments = [generated_pdf_path] + uploaded_files
    
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
    # TODO: Make this function for approvers, use roman email for TESTING
    #approvers = ldap_service.get_approvers_email("CUE-APPROVERS-GROUP")
    approvers = ["roman_campbell@lawb.uscourts.gov"]
    
    # Build payload
    items, email_payload = build_email_payload(payload)
    
    # Add approvers to payload
    email_payload.to = approvers
    email_payload.attachments = [generated_pdf_path] + uploaded_files
    
    # Send with approver template
    await smtp_service.send_approver_email(email_payload)