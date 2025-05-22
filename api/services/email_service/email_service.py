from api.services.email_service.renderer import TemplateRenderer
from api.services.email_service.transport import EmailTransport, OutlookTransport
from api.services.ldap_service import LDAPService
from api.services.email_service.models import EmailMessage
from typing import List, Optional
from api.services.email_service.models import GroupCommentPayload
import os
from jinja2 import Environment, FileSystemLoader


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
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> None:
        # Render the email template
        html_body = self.renderer.render(template_name, context)
        

        # Build the email message
        msg = EmailMessage(
                subject=subject,
                sender=self.ldap_service.get_email_address(
                    self.ldap_service.connection,
                    self.ldap_service.get_user_email(
                        self.ldap_service.connection, 
                        self.ldap_service.get_user_name())),
                to=to,
                cc=cc or [],
                html_body=html_body,
                attachments=attachments or [],
            )

        # Send the email
        self.transport.send(msg)
        
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
        
    def  build_comment_email(self, payload: GroupCommentPayload):
        """
        Build an email to the requester with the comment
        """
        template_dir = os.path.join(self.project_root, "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("comment_template.html")
        
        # Prepare the data for the template
        items = list(zip(payload.item_desc, payload.comment))
        context = {
            "groupKey": payload.groupKey,
            "items": items,
            "requestor_name": self.recipients['requester']['name']
        }
        
        # Render the template
        html = template.render(**context)
        return html
    
    # Send an email to the requester with the comment
    def send_comment_email(self, payload: GroupCommentPayload):
        """
        Send an email to the requester with the comment
        """
        
        html = self.build_comment_email(payload)
        self.send(outlook=None, to_email=self.recipients['requester']['email'], subject=f"Comments on {payload.groupKey}", body=html)

