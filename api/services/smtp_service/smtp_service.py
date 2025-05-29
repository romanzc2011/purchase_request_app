import asyncio
from email.mime.application import MIMEApplication
import mimetypes
import aiosmtplib
import sys

from api.services.smtp_service.smtp_client import AsyncSMTPClient
from loguru import logger
from api.settings import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from typing import List, Optional
from pathlib import Path

from api.services.ldap_service import LDAPService
from api.services.email_service.models import GroupCommentPayload
from api.schemas.pydantic_schemas import EmailPayload, PurchaseRequestPayload
from api.services.smtp_service.renderer import TemplateRenderer
    
class SMTP_Service:
    def __init__(
        self,
        renderer: TemplateRenderer,
        ldap_service: LDAPService,
    ):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_email_addr = settings.smtp_email_addr
        self.renderer = renderer
        self.ldap_service = ldap_service
        
    #-------------------------------------------------------------------------------
    # SEND EMAIL - async
    #-------------------------------------------------------------------------------
    async def _send_mail_async(
        self, 
        payload: EmailPayload, 
        use_approver_template: bool = False,
        use_requester_template: bool = False
        ):
        """
        Send email with asyncio, using Jinja to render the html body
        Determine the template to use based on the use_approver_template and use_requester_template parameters
        """
        
        context = {
            "ID": payload.ID,
            "requester": payload.requester,
            "datereq": payload.datereq,
            "totalPrice": sum(item.totalPrice for item in payload.email_items),
            "items": payload.email_items,  # my EmailItemsPayload
            "link_to_request": f"{settings.app_base_url}/approval"
        }
        # Determine the template to use
        if use_approver_template and not use_requester_template:
            html_body = self.renderer.render_approver_request_template(context)
            
        elif use_requester_template and not use_approver_template:
            html_body = self.renderer.render_requester_request_template(context)
        else:
            raise ValueError("Invalid template parameters")
        
        # User text body as fallback if no html body
        text_body = payload.text_body or None
        #-------------------------------------------------------------------------------
        # Pull out headers and attachments
        cc = payload.cc or []
        bcc = payload.bcc or []
        attachments = payload.attachments or []
        
        #-------------------------------------------------------------------------------
        # Build MIME 
        msg = MIMEMultipart("mixed")
        msg['Subject'] = payload.subject
        msg['From'] = payload.sender
        msg['To'] = ', '.join(payload.to)
        if cc: msg['Cc'] = ', '.join(cc)
        if bcc: msg['Bcc'] = ', '.join(bcc)
        
        #-------------------------------------------------------------------------------
        # Add HTML body
        msg.attach(MIMEText(html_body, "html"))
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        
        # Add attachments
        for file_path in attachments:
            path = Path(file_path)
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding is not None:
                maintype, subtype = "application", "octet-stream"
            else:
                maintype, subtype = ctype.split("/", 1)
            
            with open(path, "rb") as f:
                data = f.read()
            
            msg.add_attachment(
                data,
                maintype=maintype,
                subtype=subtype,
                filename=path.name  
            )
        
        #-------------------------------------------------------------------------------
        # Send wity async SMTP client
        smtp = aiosmtplib.SMTP(
            hostname=self.smtp_server,
            port=self.smtp_port,
            starttls=False,
            ssl=False,
        )
        
        async with AsyncSMTPClient(
            hostname=self.smtp_server,
            port=self.smtp_port,
            starttls=False,
            ssl=False,
            timeout=10,
        ) as smtp:
            await smtp.send_message(msg)
        