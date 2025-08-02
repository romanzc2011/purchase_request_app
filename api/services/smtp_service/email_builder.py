from abc import ABC, abstractmethod
from http.client import HTTPException
from api.schemas.approval_schemas import ApprovalRequest
from api.schemas.email_schemas import EmailPayloadRequest, LineItemsPayload
from api.schemas.ldap_schema import LDAPUser
from api.settings import settings
from api.utils.misc_utils import format_username
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.services.db_service import (
    PurchaseRequestHeader,
    PurchaseRequestLineItem,
)
from api.services.ldap_service import LDAPService

# ----------------------------------------------------------------------------------------
# EMAIL BUILDER
# ----------------------------------------------------------------------------------------
class EmailBuilder(ABC):
    @abstractmethod
    async def build_email_payload(self) -> EmailPayloadRequest:
        pass

# ----------------------------------------------------------------------------------------
# APPROVER EMAIL BUILDER
# ----------------------------------------------------------------------------------------
class ApproverEmailBuilder(EmailBuilder):
    def __init__(
        self, 
        db: AsyncSession, 
        request: ApprovalRequest,
        current_user: LDAPUser,
        ldap_service: LDAPService
    ):
        self.db = db
        self.current_user = current_user
        self.request = request
        self.ldap_service = ldap_service

    async def build_email_payload(self) -> EmailPayloadRequest:
        logger.info(f"Building email payload for {self.request.uuid}")
        # ----------------------------------------------------------------------------------------
        # BUILD EMAIL PAYLOADS
        # ----------------------------------------------------------------------------------------
        # Query purchase request line items for line_item_uuid
        stmt = (
			select(
				PurchaseRequestHeader.requester,
				PurchaseRequestHeader.datereq,
				PurchaseRequestHeader.dateneed,
				PurchaseRequestHeader.orderType,
				PurchaseRequestHeader.pdf_output_path,
				PurchaseRequestLineItem.budgetObjCode,
				PurchaseRequestLineItem.itemDescription,
				PurchaseRequestLineItem.justification,
				PurchaseRequestLineItem.location,
				PurchaseRequestLineItem.quantity,
				PurchaseRequestLineItem.priceEach,
				PurchaseRequestLineItem.totalPrice,
				PurchaseRequestLineItem.fund,
				PurchaseRequestLineItem.isCyberSecRelated,
				PurchaseRequestLineItem.uploaded_file_path
			)
			.join(PurchaseRequestLineItem, PurchaseRequestLineItem.purchase_request_id == PurchaseRequestHeader.ID)
			.where(PurchaseRequestLineItem.UUID == self.request.uuid)
		)
        result = await self.db.execute(stmt)
        rows = result.all()
        
        logger.info(f"Rows: {rows}")
        if not rows:
            raise HTTPException(status_code=404, detail="No line items found for this request")

        # Get requester email from LDAP
        requester_email = await self.ldap_service.get_email_address(rows[0].requester)

		# Build line items for email payload
        items_for_email = [
            LineItemsPayload(
                budgetObjCode=row.budgetObjCode,
                itemDescription=row.itemDescription,
                location=row.location,
                justification=row.justification,
                quantity=row.quantity,
                priceEach=row.priceEach,
                totalPrice=row.totalPrice,
                fund=row.fund
            )
            for row in rows
        ]
        
        # Build flat list of attachments from every row
        attachments: list[str] = []
        for r in rows:
            if r.uploaded_file_path:
                if isinstance(r.uploaded_file_path, (list, tuple)):
                    attachments.extend(r.uploaded_file_path)
                else:
                    attachments.append(r.uploaded_file_path)

        # --------------------------------------------------------
        # Send notification to final_approvers that they have a request to approve/deny
        email_request_payload = EmailPayloadRequest(
            model_type="email_request",
            ID=self.request.id,
            requester=format_username(rows[0].requester),
            requester_email=requester_email,
            datereq=rows[0].datereq,
            dateneed=rows[0].dateneed,
            orderType=rows[0].orderType,
            subject=f"Purchase Request #{self.request.id}",
            sender=settings.smtp_email_addr,
            to=None,    # Assign this in the smtp service
            cc=None,    # Assign this in the smtp service
            bcc=None,
            text_body=None,
            approval_link=f"{settings.link_to_request}",
            items=items_for_email,
            attachments=attachments
        )
        logger.info(f"Email request payload: {email_request_payload}")
        return email_request_payload