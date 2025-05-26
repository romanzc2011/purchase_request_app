from api.services.email_service.renderer import TemplateRenderer
from api.services.email_service.transport import EmailTransport, OutlookTransport
from api.services.ldap_service import LDAPService
from api.services.email_service.models import EmailMessage
from api.services.ldap_service import LDAPUser
from typing import List, Optional
from api.services.email_service.models import GroupCommentPayload
import os
from jinja2 import Environment, FileSystemLoader

# TODO: Make email addr data structs for choosing email addr dynamically/programmatically

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

        # Build the email message
        msg = EmailMessage(
                subject=subject,
                sender = "Purchase Request System",
                to=to,
                cc=cc or [],
                html_body=html_body,
                attachments=attachments or [],
            )

        # Send the email
        self.transport.send(msg)
        
    ##############################################################
    # NOTIFY NEW REQUEST
    ##############################################################
    def notify_new_request(self, lawb_id: str) -> None:
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
            template_name="new_request_notification.html",
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
            template_name="comment_template.html",
            context={
                "groupKey": payload.groupKey,
                "items": list(zip(payload.item_desc, payload.comment)),
                "requestor_name": requester_name
            },
            current_user=None  # This should be passed from the caller if needed
        )

