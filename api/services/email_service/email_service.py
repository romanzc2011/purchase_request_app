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
        
   ###################################################################
    # Email sending methods
    ################################################################### 
    # def send_template_email(
    #     self,
    #     to: List[str],
    #     subject: str,
    #     template_name: str,
    #     context: dict,
    #     cc: Optional[List[str]] = None,
    #     bcc: Optional[List[str]] = None,
    #     attachments: Optional[List[str]] = None,
    #     link_to_request: Optional[str] = None,
    # ) -> None:
    #     # Render the email template
    #     html_body = self.renderer.render(template_name, context)

    #     link_to_request = f"{settings.app_base_url}/approvals"
    #     # Build the email message
    #     msg = EmailMessage(
    #             subject=subject,
    #             sender = "Purchase Request System",
    #             to=to,
    #             cc=cc or [],
    #             html_body=html_body,
    #             attachments=attachments or [],
    #             link_to_request=link_to_request
    #         )
        
    #     # Send the email
    #     self.transport.send(msg)
        
    ##############################################################
    # SEND NEW REQUEST EMAIL - to requester
    ##############################################################
    # def send_new_request(self, payload: EmailItemsPayload, current_user: LDAPUser) -> None:
    #     # This is the email that goes to the requester when they submit a new request
    #     # Fetch request details from the database
    #     logger.info("#############################################")
    #     logger.info("send_new_request")
    #     logger.info("#############################################")
        
    #     # Prepare the email context
    #     context = {
    #         'request_id': payload.request_id,
    #         'requester_name': payload.requester_name,
    #         'status': payload.status,
    #     }
    #     logger.info(f"context: {context}")
        
    #     # Send the email
    #     self.send_template_email(
    #         to=[payload.to],
    #         subject=f"New Request Notification - {payload.request_id}",
    #         template_name="requester_request_submitted.html",
    #         context=context,
    #         link_to_request=f"{settings.app_base_url}/approvals",
    #         current_user=current_user
    #     )
        
        # Render the email template
        #html_body = self.renderer.render("approver_new_request.html", context)
        
        # to = ["roman_campbell@lawb.uscourts.gov"]
        # subject = f"New Request Notification - {payload.ID}"
        
        # # Build the email message
        # msg = EmailMessage(
        #     subject=subject,
        #     sender="Purchase Request System",
        #     to=to,
        #     cc=None,  # Add cc if needed in payload
        #     bcc=None,  # Add bcc if needed in payload
        #     html_body=html_body,
        #     attachments=payload.file_attachments,
        #     link_to_request=link_to_request,
        #     context=context
        # )
        
        # # Send the email
        # self.transport.send(msg)
        
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
            current_user=None,  # This should be passed from the caller if needed
            link_to_request=f"{settings.app_base_url}/approvals"
        )
        
    ##############################################################
    # SEND APPROVAL EMAIL
    ##############################################################
    def send_approval_email(self, payload: EmailPayload):
        logger.info("#############################################")
        logger.info("send_approval_email")
        logger.info("#############################################")
        """
        Send an email to the requester with the approval
        
        Args:
            payload: The approval payload containing the approval and item descriptions
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
        self.transport.send(msg)
        
    def get_email_items(self, payload: EmailItemsPayload) -> EmailItemsPayload:
        return(EmailItemsPayload(
            ID=payload.ID,
            requester=payload.requester,
            datereq=payload.datereq,
            totalPrice=payload.totalPrice,
            itemDescription=payload.itemDescription,
            quantity=payload.quantity,
            priceEach=payload.priceEach,
        ))

    def send_new_request_to_requester(self, payload: PurchaseRequestPayload) -> None:
        """
        Send an email to the requester when they submit a new request
        """
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
                    "requester": payload.requester,
                    "request_id": payload.items[0].ID,
                    "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "items": email_items
                }
            )
        )
        
        # Send the email
        self.transport.send(msg)

    def send_new_request_to_approvers(self, payload: PurchaseRequestPayload) -> None:
        """
        Send an email to approvers when a new request is submitted
        """
        # For now, hardcode the approver email for testing
        approver_email = "roman_campbell@lawb.uscourts.gov"  # TESTING ONLY
        
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
            subject=f"New Purchase Request - {payload.items[0].ID}",
            sender="Purchase Request System",
            to=[approver_email],
            link_to_request=f"{settings.app_base_url}/approvals",
            html_body=self.renderer.render(
                "approver_new_request.html",
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
        
        # Send the email
        self.transport.send(msg)
        
        