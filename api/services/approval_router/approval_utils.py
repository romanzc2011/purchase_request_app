import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.schemas.approval_schemas import ApprovalRequest
from api.services.smtp_service.email_builder import ApproverEmailBuilder
from api.schemas.enums import AssignedGroup, ItemStatus
import api.services.db_service as dbas
from api.dependencies.pras_dependencies import smtp_service
from loguru import logger

class ApprovalUtils:
    @staticmethod
    async def get_approval_data(db: AsyncSession, uuid: str):
        stmt = select(dbas.Approval.UUID, dbas.PendingApproval.pending_approval_id).join(
            dbas.PendingApproval,
            dbas.PendingApproval.approvals_uuid == dbas.Approval.UUID
        ).where(
            dbas.PendingApproval.line_item_uuid == uuid
        )
        result = await db.execute(stmt)
        return result.first()
    
    @staticmethod
    async def insert_pending_approval(db: AsyncSession, approvals_uuid: str, request: ApprovalRequest, pending_approval_id: str):
        await dbas.insert_final_approval(
            db=db,
            approvals_uuid=approvals_uuid,
            purchase_request_id=request.id,
            line_item_uuid=request.uuid,
            pending_approval_id=pending_approval_id,
            status=ItemStatus.PENDING_APPROVAL,
            deputy_can_approve=dbas.can_deputy_approve(request.total_price),
            pending_approved_by=request.approver,
            final_approved_by=request.approver
        )
        
    @staticmethod
    async def update_final_approval(db: AsyncSession, approvals_uuid: str, request: ApprovalRequest, pending_approval_id: int):
        await dbas.update_final_approval_status(
            db=db,
            approvals_uuid=approvals_uuid,
            pending_approval_id=pending_approval_id,
            status=ItemStatus.APPROVED,
            final_approved_by=request.approver,
            final_approved_at=dbas.utc_now_truncated()
        )
    
    @staticmethod
    async def build_and_send_email(group: str, db, request, current_user, ldap_service):
        builder = ApproverEmailBuilder(db, request, current_user, ldap_service)
        payload = await builder.build_email_payload()
        await smtp_service.send_approver_email(payload, db=db, send_to=group)