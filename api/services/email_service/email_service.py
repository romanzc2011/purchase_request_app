from api.services.email_service.renderer import TemplateRenderer
from api.services.email_service.transport import EmailTransport
from api.services.ldap_service import LDAPService
from api.services.email_service.models import EmailMessage
from typing import List, Optional


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
                sender=self.ldap_service.get_user_email(),
                to=to,
                cc=cc or [],
                html_body=html_body,
                attachments=attachments or [],
            )

        # Send the email
        self.transport.send(msg)
        
    def notify_new_request(self, request_id: ID) -> None:
        # Fetch request details from the database
        request = self.ldap_service.get_request_by_id(request_id)
        
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
