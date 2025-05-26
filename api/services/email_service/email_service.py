from api.services.email_service.renderer import TemplateRenderer
from api.services.email_service.transport import EmailTransport, OutlookTransport
from api.services.ldap_service import LDAPService
from api.services.email_service.models import EmailMessage
from api.services.ldap_service import LDAPUser
from api.schemas.pydantic_schemas import EmailPayload
from typing import List, Optional
from api.services.email_service.models import GroupCommentPayload
import os
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
from api.settings import settings
# TODO: Make email addr data structs for choosing email addr dynamically/programmatically

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
    embedded_images: Optional[List[dict]] = None

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
        
   ###################################################################
    # Email sending methods
    ################################################################### 
    def send_template_email(
        self,
        to: List[str],
        subject: str,
        template_name: str,
        context: dict,
        current_user: LDAPUser,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> None:
        # Render the email template
        html_body = self.renderer.render(template_name, context)

        # Add embedded images if needed
        embedded_images = []
        if template_name == "requester_request_submitted.html":
            seal_path = os.path.join(os.path.dirname(__file__), "templates", "seal_no_border.png")
            if os.path.exists(seal_path):
                embedded_images.append({
                    "path": seal_path,
                    "cid": "seal_no_border"
                })

        # Build the email message
        msg = EmailMessage(
                subject=subject,
                sender = "Purchase Request System",
                to=to,
                cc=cc or [],
                html_body=html_body,
                attachments=attachments or [],
                embedded_images=embedded_images
            )

        # Send the email
        self.transport.send(msg)
        
    ##############################################################
    # NOTIFY NEW REQUEST
    ##############################################################
    def notify_new_request(self, lawb_id: str) -> None:
        # This is the email that goes to the requester when they submit a new request
        # Fetch request details from the database
        request = self.ldap_service.get_request_by_id(lawb_id)
        
        # Prepare the email context
        context = {
            'request_id': request.id,
            'requester_name': request.requester_name,
            'request_date': request.request_date,
            'status': request.status,
        }
        
        # Send the email
        self.send_template_email(
            to=[request.requester_email],
            subject=f"New Request Notification - {request.id}",
            template_name="requester_request_submitted.html",
            context=context,
        )
        
    ##############################################################
    # SEND COMMENT EMAIL
    ##############################################################
    def send_comment_email(self, payload: GroupCommentPayload, requester_email: str, requester_name: str):
        """
        Send an email to the requester with the comment
        
        Args:
            payload: The comment payload containing the comments and item descriptions
            requester_email: The email address of the requester
            requester_name: The name of the requester
        """
        self.send_template_email(
            to=[requester_email],
            subject=f"Comments on {payload.groupKey}",
            template_name="requester_comment_template.html",
            context={
                "groupKey": payload.groupKey,
                "items": list(zip(payload.item_desc, payload.comment)),
                "requestor_name": requester_name
            },
            current_user=None  # This should be passed from the caller if needed
        )
        
    ##############################################################
    # SEND APPROVAL EMAIL
    ##############################################################
    def send_approval_email(self, payload: EmailPayload):
        """
        Send an email to the requester with the approval
        
        Args:
            payload: The approval payload containing the approval and item descriptions
        """
        # absolute url to the request
        link_to_request = f"{settings.app_base_url}/approvals"
        
        context = {
            "request_id": payload.request_id if hasattr(payload, "request_id") else None,
            "requester_name": payload.requester_name,
            "status": payload.status,
            "message": payload.message,
            "approver_name": payload.approver_name,
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
        self.transport.send(msg)
        
        