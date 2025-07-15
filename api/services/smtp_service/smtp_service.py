from email.mime.image import MIMEImage
import mimetypes
import os
import aiosmtplib

from loguru import logger
from api.settings import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple
from pathlib import Path
from email.mime.application import MIMEApplication
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.services.cache_service import cache_service
from api.services.ldap_service import LDAPService
from api.schemas.email_schemas import ValidModel, EmailPayloadComment, EmailPayloadRequest
from api.schemas.comment_schemas import GroupCommentPayload
from api.services.smtp_service.renderer import TemplateRenderer
from api.settings import settings
import api.services.db_service as dbas
from api.utils.misc_utils import get_justifications_and_comments
from api.services.progress_bar_state import ProgressBar

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
        self.logo_file_path = os.path.join(settings.BASE_DIR, "src", "assets", "seal_no_border.png")
        
    #-------------------------------------------------------------------------------
    # SEND EMAIL - async
    #-------------------------------------------------------------------------------
    async def _send_mail_async(
        self, 
        payload: ValidModel,
        db: AsyncSession,
        to_address: Optional[str] = None,
        cc_address: Optional[str] = None,
        use_approver_template: Optional[bool] = False,
        use_requester_template: Optional[bool] = False,
        use_comment_template: Optional[bool] = False,
        use_approved_template: Optional[bool] = False,
    ):
        """
        Send email with asyncio, using Jinja to render the html body
        Determine the template to use based on the template parameters
        """
        logger.info("#############################################################")
        logger.info("_SEND_MAIL_ASYNC")
        logger.info("#############################################################")
        
        additional_comments = await get_justifications_and_comments(db, payload.ID)
        
        # Email payload request
        if isinstance(payload, EmailPayloadRequest):
            # Get CO data from database
            contracting_officer = await dbas.get_contracting_officer_by_id(db, payload.ID)
            
            context = {
                "ID": payload.ID,
                "requester": payload.requester,
                "datereq": payload.datereq,
                "dateneed": payload.dateneed,
                "orderType": payload.orderType,
                "additional_comments": additional_comments,
                "items": payload.items,
                "totalPrice": sum(item.totalPrice for item in payload.items),
                "CO": contracting_officer,
                "contracting_officer": contracting_officer
            }
            logger.warning(f"CONTEXT EMAIL PAYLOAD REQUEST: {context}")

        # Email payload comment
        if isinstance(payload, EmailPayloadComment):
            # Format items for the template (zip item descriptions with comments)
            items = []
            for comment_group in payload.comment_data:
                for desc, comment in zip(comment_group.item_desc, comment_group.comment):
                    items.append((desc, comment))
            logger.warning(f"CONTEXT EMAIL PAYLOAD COMMENT: {payload}")
            context = {
                "groupKey": payload.ID,
                "requestor_name": payload.requester,
                "items": items,
            }
            
        #-------------------------------------------------------------------------------
        # Build MIME
        #-------------------------------------------------------------------------------
        logger.info("Building MIME..")
        msg_root = MIMEMultipart("related")
        msg_root['Subject'] = payload.subject
        msg_root['From'] = "it@lawb.uscourts.gov"
        
        # APPROVER TEMPLATE
        if use_approver_template and not use_requester_template and not use_comment_template and not use_approved_template:
            if to_address:
                tos = to_address if isinstance(to_address, list) else [to_address]
                msg_root['To'] = ', '.join(tos)
                
            if cc_address:
                ccs = cc_address if isinstance(cc_address, list) else [cc_address]
                msg_root['Cc'] = ', '.join(ccs)
            
            html_body = self.renderer.render_approver_request_template(context)
        
        # REQUESTER TEMPLATE
        elif use_requester_template and not use_approver_template and not use_comment_template and not use_approved_template:
            msg_root['To'] = payload.requester_email
            html_body = self.renderer.render_requester_request_template(context)
            
        # APPROVED TEMPLATE
        elif use_approved_template and not use_approver_template and not use_requester_template and not use_comment_template:
            msg_root['To'] = payload.requester_email
            html_body = self.renderer.render_requester_approved_template(context)
            
        # COMMENT TEMPLATE
        elif use_comment_template and not use_approver_template and not use_requester_template and not use_approved_template:
            msg_root['To'] = payload.requester_email
            html_body = self.renderer.render_comment_template(context)
            
        else:
            raise ValueError("Invalid template parameters")
 
        # Attach HTML as alternative
        msg_alt = MIMEMultipart("alternative")
        msg_root.attach(msg_alt)
        
        # Create HTML body and attach to alternative
        html_body = MIMEText(html_body, "html")
        msg_alt.attach(html_body)
        
        # Read PNG bytes of logo file
        logo_data = Path(self.logo_file_path).read_bytes()
        
        # Attach logo as related part to HTML
        logo_attachment = MIMEImage(logo_data, _subtype="png")
        logo_attachment.add_header("Content-ID", "<seal_no_border>")
        logo_attachment.add_header("Content-Disposition", "inline", filename="seal_no_border.png")
        msg_root.attach(logo_attachment)
        
        # User text body as fallback if no html body
        text_body = payload.text_body or None
        #-------------------------------------------------------------------------------
        # Pull out headers and attachments
        bcc = payload.bcc or []
        
        if bcc: msg_root['Bcc'] = ', '.join(bcc)
        logger.info(f"PAYLOAD, look for email: {payload}")
        #-------------------------------------------------------------------------------
        # Add HTML body
        if text_body:
            msg_root.attach(MIMEText(text_body, "plain"))
        logger.info("Message attached to email")
        
        logger.info(f"PAYLOAD, look for attachments: {payload}")
        # Add attachments only for request emails
        if isinstance(payload, EmailPayloadRequest) and payload.attachments:
            for file_path in payload.attachments:
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
                msg_root.attach(attachment)
        
        #-------------------------------------------------------------------------------
        logger.info("Sending multipart message")
        smtp_client = aiosmtplib.SMTP(
            hostname=self.smtp_server,
            port=25,
            start_tls=False,
            use_tls=False,
        )
        async with smtp_client:
            result = await smtp_client.send_message(msg_root)
            logger.info(f"RESULT: {result}")
        
    #-------------------------------------------------------------------------------
    # Email Wrappers
    async def send_approver_email(
        self, 
        payload: EmailPayloadRequest, 
        db: AsyncSession, 
        send_to: str = None):
        """
        Send email to approvers
        """
        logger.debug(f"SENDING TO: {send_to} send_approver_email")
        if send_to == "IT":
            # Send to Matt (IT) for testing romancampbell
            #to_address = "matthew_strong@lawb.uscourts.gov"
            # TESTING
            logger.debug("Sending to Roman for testing, but in prod we send to Matt")
            to_address = ["roman_campbell@lawb.uscourts.gov"]
        elif send_to == "FINANCE":
            #to_address = ["Lela_Robichaux@lawb.uscourts.gov"]
            # TESTING
            logger.debug("Sending to Roman for testing, but in prod we send to Lela")
            to_address = ["roman_campbell@lawb.uscourts.gov"]
        else:
            #to_address = ["Peter_Baltz@lawb.uscourts.gov", "Lauren_Lee@lawb.uscourts.gov"]
            to_address = ["roman_campbell@lawb.uscourts.gov"]
            logger.debug(f"SENDING TO: {to_address} send_approver_email")
            
        await self._send_mail_async(
            payload,
            db=db,
            to_address=to_address,
            use_approver_template=True,
            use_requester_template=False,
            use_comment_template=False,
            use_approved_template=False
        )   

    async def send_requester_email(self, payload: EmailPayloadRequest, db: AsyncSession):
        """
        Send email to requester
        """
        
        await self._send_mail_async(
            payload,
            db=db,
            use_approver_template=False,
            use_requester_template=True,
            use_comment_template=False,
            use_approved_template=False
        )
        
    async def send_request_approved_email(self, payload: EmailPayloadRequest, db: AsyncSession):
        """
        Send email to requester that their request has been approved
        """
        logger.debug("SENDING REQUEST APPROVED EMAIL")
        await self._send_mail_async(
            payload=payload,
            db=db,
            use_approver_template=False,
            use_requester_template=False,
            use_comment_template=False,
            use_approved_template=True
        )
        
    #-------------------------------------------------------------------------------
    # Email Wrappers - COMMENTS
    async def send_comments_email(self, payload: EmailPayloadComment, db: AsyncSession):
        """
        Send comments
        """
        await self._send_mail_async(
            payload=payload,
            db=db,
            use_approver_template=False,
            use_requester_template=False,
            use_comment_template=True
        )