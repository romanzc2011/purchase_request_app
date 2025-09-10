from email.mime.image import MIMEImage
import mimetypes
import os
import aiosmtplib
import asyncio
import json

from loguru import logger
from api.settings import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from email.mime.application import MIMEApplication
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Sequence
from sqlalchemy import select

from api.services.ldap_service import LDAPService
from api.schemas.email_schemas import ValidModel, EmailPayloadComment, EmailPayloadRequest
from api.services.smtp_service.renderer import TemplateRenderer
from api.settings import settings
import api.services.db_service as dbas
from api.utils.misc_utils import get_justifications_and_comments
from api.schemas.enums import AssignedGroup
from api.services.ipc_status import ipc_status
from api.services.socketio_server.sio_instance import sio
from api.services.ipc_status import ipc_status

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
        additional_comments = await get_justifications_and_comments(db, payload.ID)
        
        # Email payload request
        if isinstance(payload, EmailPayloadRequest):
            # Get CO data from database
            contracting_officer = await dbas.get_contracting_officer_by_id(db, payload.ID)
            
            context = {
                "ID": payload.ID,
                "requester": payload.requester,
                "datereq": payload.datereq,
                "approval_date": payload.approval_date,
                "orderType": payload.orderType,
                "additional_comments": additional_comments,
                "items": payload.items,
                "totalPrice": sum(item.totalPrice for item in payload.items),
                "CO": contracting_officer,
                "contracting_officer": contracting_officer
            }

        # Email payload comment
        if isinstance(payload, EmailPayloadComment):
            # Format items for the template (zip item descriptions with comments)
            items = []
            for comment_group in payload.comment_data:
                for desc, comment in zip(comment_group.item_desc, comment_group.comment):
                    items.append((desc, comment))
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

        #-------------------------------------------------------------------------------
        # REQUESTER TEMPLATE
        #-------------------------------------------------------------------------------
        elif use_requester_template and not use_approver_template and not use_comment_template and not use_approved_template:
            msg_root['To'] = payload.requester_email
            html_body = self.renderer.render_requester_request_template(context)
            
        #-------------------------------------------------------------------------------
        # APPROVED TEMPLATE
        #-------------------------------------------------------------------------------
        elif use_approved_template and not use_approver_template and not use_requester_template and not use_comment_template:
            msg_root['To'] = payload.requester_email
            html_body = self.renderer.render_requester_approved_template(context)
            
        #-------------------------------------------------------------------------------
        # COMMENT TEMPLATE
        #-------------------------------------------------------------------------------
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
        #-------------------------------------------------------------------------------
        # Add HTML body
        if text_body:
            msg_root.attach(MIMEText(text_body, "plain"))
        logger.info("Message attached to email")
        
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
    # SEND EMAIL TO APPROVERS
    #-------------------------------------------------------------------------------
    async def send_approver_email(
        self, 
        payload: EmailPayloadRequest, 
        db: AsyncSession, 
        send_to: list[AssignedGroup] | None = None):
        """
        Send email to approvers
        """
        logger.debug(f"SENDING TO: {send_to} send_approver_email")
        
        # Normalizing input - handle both strings and lists
        if isinstance(send_to, str):
            roles = [send_to]
        elif isinstance(send_to, (list, tuple)):
            roles = list(send_to)
        else:
            roles = []
        
        # Initialize to_address with a default value
        to_address = []
        cc_address = []
        to_username = []
        cc_username = []
        
        logger.info(f"SEND_TO: {send_to}")
        
        for role in roles:
            logger.debug(f"ROLE: {role}")
            match role:
                case AssignedGroup.IT.value:
                    # Send to IT
                    to, to_users = await self.get_toaddr(department=AssignedGroup.IT.value, db=db)
                    cc, cc_users = await self.get_toaddr(department=AssignedGroup.FINANCE.value, db=db)
                    to_address.extend(to)
                    cc_address.extend(cc)
                    to_username.extend(to_users)
                    cc_username.extend(cc_users)
                    
                case AssignedGroup.FINANCE.value:
                    # Query WorkflowUser table for finance users and see if active
                    # Lauren Lee, Peter Baltz
                    to, to_users = await self.get_toaddr(department=AssignedGroup.FINANCE.value, db=db)
                    cc, cc_users = await self.get_toaddr(department=AssignedGroup.FINANCE.value, db=db)
                    to_address.extend(to)
                    cc_address.extend(cc)
                    to_username.extend(to_users)
                    cc_username.extend(cc_users)
                    
                case AssignedGroup.MANAGEMENT.value:
                    # Send to Management
                    to, to_users = await self.get_toaddr(department=AssignedGroup.MANAGEMENT.value, db=db)
                    deputy_clerk_addresses, deputy_clerk_username = await self.get_toaddr(department=AssignedGroup.DEPUTY_CLERK.value, db=db)
                    to_address.extend(to)
                    to_address.extend(deputy_clerk_addresses)  # Because deputy_clerk is also in management team
                    cc, cc_users = await self.get_toaddr(department=AssignedGroup.FINANCE.value, db=db)
                    to_username.extend(to_users)
                    to_username.extend(deputy_clerk_username)
                    cc_address.extend(cc)
                    cc_username.extend(cc_users)
                    
                case AssignedGroup.DEPUTY_CLERK.value:
                    # Send to deputy clerk
                    to, to_users = await self.get_toaddr(department=AssignedGroup.DEPUTY_CLERK.value, db=db)
                    cc, cc_users = await self.get_toaddr(department=AssignedGroup.FINANCE.value, db=db)
                    to_address.extend(to)
                    cc_address.extend(cc)
                    to_username.extend(to_users)
                    cc_username.extend(cc_users)
                    
                case AssignedGroup.CHIEF_CLERK.value:
                    # Send to chief clerk
                    to, to_users = await self.get_toaddr(department=AssignedGroup.CHIEF_CLERK.value, db=db)
                    cc, cc_users = await self.get_toaddr(department=AssignedGroup.FINANCE.value, db=db)
                    to_address.extend(to) 
                    cc_address.extend(cc)   
                    to_username.extend(to_users)
                    cc_username.extend(cc_users)
                    
                case _:
                    # Default case, most likely testing
                    logger.debug(f"Unknown recipient role: {role}")
        
        logger.info(f"SENDING TO: {to_address} :: {to_username}")
        logger.info(f"CC TO:     {cc_address} :: {cc_username}")
        await ipc_status.update(field="approval_email_sent", value=True)  # To inform progress bar that email has been sent
        await self._send_mail_async(
            payload,
            db=db,
            to_address=to_address,
            cc_address=cc_address,
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
    #-------------------------------------------------------------------------------
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
        
    #-------------------------------------------------------------------------------
    # Retrieve to_addresses based on department and active
    #-------------------------------------------------------------------------------
    async def get_toaddr(self, department: str, db: AsyncSession):
        stmt = select(dbas.WorkflowUser.email, dbas.WorkflowUser.username).where(
            dbas.WorkflowUser.department == department,
            dbas.WorkflowUser.active == True
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        to_address = []
        username = []
        
        for email, uname in rows:
            to_address.append(email)
            username.append(uname)
            
        return to_address, username