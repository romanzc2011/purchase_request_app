from datetime import datetime
import mimetypes
import asyncio
import aiosmtplib

from api.services.smtp_service.smtp_client import AsyncSMTPClient
from loguru import logger
from api.settings import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from typing import List, Tuple
from pathlib import Path
from email.mime.application import MIMEApplication

from api.services.ldap_service import LDAPService
from api.schemas.comment_schemas import GroupCommentPayload
from api.schemas.email_schemas import EmailPayload, LineItemsPayload
from api.services.smtp_service.renderer import TemplateRenderer
from api.schemas.purchase_schemas import PurchaseItem, PurchaseRequestPayload
from api.services.smtp_service.builders import build_email_payload
    
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
            "totalPrice": sum(i.totalPrice for i in payload.items),
            "items": payload.items,
            "link_to_request": payload.approval_link or f"{settings.app_base_url}/approval",
            "comments": payload.comments,
            "current_year": datetime.now().year,
        }
        
        logger.info(f"CONTEXT: {context}")
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
        logger.info("Building MIME..")
        msg = MIMEMultipart("mixed")
        msg['Subject'] = payload.subject
        msg['From'] = "romanzc2011@gmail.com"
        msg['To'] = "roman_campbell@lawb.uscourts.gov"
        # if cc: msg['Cc'] = ', '.join(cc)
        # if bcc: msg['Bcc'] = ', '.join(bcc)
        
        #-------------------------------------------------------------------------------
        # Add HTML body
        msg.attach(MIMEText(html_body, "html"))
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        logger.info("Message attached to email")
        
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
            
            attachment = MIMEApplication(data, _subtype=subtype)
            attachment.add_header('Content-Disposition', 'attachment', filename=path.name)
            msg.attach(attachment)
        
        #-------------------------------------------------------------------------------
        logger.info("Sending multipart message")
        smtp_client = aiosmtplib.SMTP(
            hostname=self.smtp_server,
            port=25,
            start_tls=False,
            use_tls=False,
        )
        async with smtp_client:
            result = await smtp_client.send_message(msg)
            logger.info(f"RESULT: {result}")
        
    #-------------------------------------------------------------------------------
    # Email Wrappers
    async def send_approver_email(self, payload: EmailPayload):
        """
        Send email to approvers
        """
        await self._send_mail_async(
            payload,
            use_approver_template=True,
            use_requester_template=False
        )   

    async def send_requester_email(self, payload: EmailPayload):
        """
        Send email to requester
        """
        logger.info("In send_requester_email")
        await self._send_mail_async(
            payload,
            use_approver_template=False,
            use_requester_template=True
        )