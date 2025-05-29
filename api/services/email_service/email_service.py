import asyncio
import dataclasses
from datetime import date, datetime
from api.services.email_service.renderer import TemplateRenderer
from api.services.email_service.transport import EmailTransport
from api.services.ldap_service import LDAPService
from api.services.email_service.models import EmailMessage
from api.services.ldap_service import LDAPUser
from api.schemas.pydantic_schemas import EmailPayload, PurchaseRequestPayload
from typing import List, Optional
from api.services.email_service.models import GroupCommentPayload
from loguru import logger
from dataclasses import dataclass
from api.settings import settings
# TODO: Make email addr data structs for choosing email addr dynamically/programmatically

@dataclass
class EmailItemsPayload:
    ID: str
    requester: str
    datereq: date
    totalPrice: float
    itemDescription: str
    quantity: int
    priceEach: float
    link_to_request: Optional[str] = None
    
@dataclass
class EmailMessage:
    subject: str
    sender: str
    to: List[str]
    link_to_request: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    attachments: Optional[List[str]] = None
    email_items: Optional[EmailItemsPayload] = None
    
class EmailService:
    def __init__(
        self,
        renderer: TemplateRenderer,
        transport: EmailTransport,
        ldap_service: LDAPService,
    ):
        self.renderer = renderer
        self.transport = transport
        self.ldap_service = ldap_service
        
    ##############################################################
    # SEND COMMENT EMAIL
    ##############################################################
    async def send_comment_email(self, payload: GroupCommentPayload, requester_email: str, requester_name: str):
        """
        Send an email to the requester with the comment
        
        Args:
            payload: The comment payload containing the comments and item descriptions
            requester_email: The email address of the requester
            requester_name: The name of the requester
        """
        await self.send_template_email(
            to=[requester_email],
            subject=f"Comments on {payload.groupKey}",
            template_name="requester_comment_template.html",
            context={
                "groupKey": payload.groupKey,
                "items": list(zip(payload.item_desc, payload.comment)),
                "requestor_name": requester_name
            },
            current_user=None,  # This should be passed from the caller if needed
            link_to_request=f"{settings.app_base_url}/approvals"
        )
        
    ##############################################################
    # SEND APPROVAL EMAIL
    ##############################################################
    async def send_approval_email(self, payload: EmailPayload):
        logger.info("#############################################")
        logger.info("send_approval_email")
        logger.info("#############################################")
        """
        Send an email to the requester with the approval
        
        Args:
            payload: The approval payload containing the approval and item descriptions
        """
        # absolute url to the request
        link_to_request = f"{settings.app_base_url}/approvals"
        
        logger.info(f"Payload: {payload}")
        
        context = {
            "request_id": payload.request_id if hasattr(payload, "request_id") else None,
            "requester_name": payload.requester_name,
            "status": payload.status,
            "message": payload.message,
            "link_to_request": link_to_request,
            "items": payload.items if hasattr(payload, "items") else [],
        }
        payload.to = ["roman_campbell@lawb.uscourts.gov"]
        # Render the email template
        html_body = self.renderer.render("approval_email.html", context)
        
        # Build the email message
        msg = EmailMessage(
            subject=payload.subject,
            sender="Purchase Request System",
            to=payload.to,
            cc=None,  # Add cc if needed in payload
            bcc=None,  # Add bcc if needed in payload
            html_body=html_body,
            attachments=payload.file_attachments,
            link_to_request=link_to_request,
        )
        
        # Send the email
        await self.transport.send(msg)

    async def send_new_request_to_requester(self, payload: PurchaseRequestPayload) -> None:
        """
        Send an email to the requester when they submit a new request
        """
        logger.info("#############################################")
        logger.info("send_new_request_to_requester")
        logger.info("#############################################")
        
        # Get requester's email from LDAP
        requester_email = self.ldap_service.get_email_address(
            self.ldap_service.get_connection(), 
            payload.requester
        )
        
        if not requester_email:
            logger.error(f"Could not find email for requester {payload.requester}")
            return

        # Prepare email items
        email_items = []
        for item in payload.items:
            email_items.append(EmailItemsPayload(
                ID=item.ID,
                requester=item.requester,
                datereq=item.datereq,
                totalPrice=item.totalPrice,
                itemDescription=item.itemDescription,
                quantity=item.quantity,
                priceEach=item.priceEach,
                link_to_request=f"{settings.app_base_url}/approvals"
            ))

        # Build the email message
        msg = EmailMessage(
            subject=f"Purchase Request Submitted - {payload.items[0].ID}",
            sender="Purchase Request System",
            to=[requester_email],
            link_to_request=f"{settings.app_base_url}/approvals",
            html_body=self.renderer.render(
                "requester_request_submitted.html",
                {
                    "ID": payload.items[0].ID,
                    "requester": payload.requester,
                    "datereq": payload.items[0].datereq,
                    "totalPrice": sum(item.totalPrice for item in payload.items),
                    "items": email_items,
                    "link_to_request": f"{settings.app_base_url}/approvals"
                }
            )
        )
        
        try:
            # Send the email and await the result
            await self.transport.send(msg)
            logger.info(f"Sent confirmation email to requester: {requester_email}")
        except Exception as e:
            logger.error(f"Error sending email to requester {requester_email}: {e}")
            raise

    async def send_new_request_to_approvers(self, payload: PurchaseRequestPayload, pdf_path: str, upload_paths: List[str] = None) -> None:
        """Send email to approvers with the new request details and attachments."""
        try:
            logger.info("#############################################")
            logger.info("send_new_request_to_approvers")
            logger.info("#############################################")
            # Get approver emails from LDAP
            #approver_emails = self.ldap_service.get_approver_emails()
            approver_emails = ["roman_campbell@lawb.uscourts.gov"]
            if not approver_emails:
                logger.error("No approver emails found")
                return

            email_items = []
            for item in payload.items:
                # Prepare email context
                context = {
                    "ID": item.ID,
                    "requester": item.requester,
                    "datereq": item.datereq,
                    "items": [
                        {
                            "itemDescription": item.itemDescription,
                            "quantity": item.quantity,
                            "priceEach": item.priceEach,
                            "totalPrice": item.totalPrice,
                            "link_to_request": f"{settings.app_base_url}/approvals/{item.ID}"
                        }
                    ]
                }

                # Create list of attachments
                attachments = [pdf_path]  # Always include the PDF
                if upload_paths:  # Add any uploaded files
                    attachments.extend(upload_paths)
                
                logger.info(f"Sending email with attachments: {attachments}")

                # Create email message
                message = EmailMessage(
                    subject=f"New Purchase Request {item.ID} from {item.requester}",
                    sender="Purchase Request System",
                    to=approver_emails,
                    link_to_request=f"{settings.app_base_url}/approvals",
                    html_body=self.renderer.render("approver_new_request.html", context),
                    attachments=attachments
                )

                # Send email to each approver
                for addr in approver_emails:
                    try:
                        # Create a copy of the message for each recipient
                        individual_message = dataclasses.replace(message, to=[addr])
                        # Send email and await the result
                        await self.transport.send(individual_message)
                        logger.info(f"Sent email to approver: {addr}")
                    except Exception as e:
                        logger.error(f"Error sending email to {addr}: {e}")
                        continue

                logger.info(f"Completed sending emails to {len(approver_emails)} approvers")
        except Exception as e:
            logger.error(f"Error in send_new_request_to_approvers: {e}")
            raise
        
        