from __future__ import annotations
import asyncio
from http.client import HTTPException
from typing import Optional
from abc import ABC, abstractmethod
from api import settings
from api.schemas.email_schemas import EmailPayloadRequest, LineItemsPayload
from api.services import cache_service
from api.dependencies.pras_dependencies import smtp_service
from api.utils.misc_utils import format_username
from loguru import logger
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
import api.services.db_service as dbas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from api.schemas.ldap_schema import LDAPUser
from api.services.approval_router.approver_policy import ApproverPolicy
from api.services.smtp_service.email_builder import ApproverEmailBuilder
from api.services.ldap_service import LDAPService


# Approval Router to determine the routing of requests
class Handler(ABC):
    def __init__(self):
        logger.info(f"Handler initialized")
        self._next: Optional["Handler"] = None
        
    def set_next(self, handler: "Handler") -> "Handler":
        logger.info(f"Setting next handler: {handler}")
        self._next = handler
        return handler
    
    @abstractmethod
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser,
        ldap_service: LDAPService
    ) -> ApprovalRequest:
        
        logger.debug(f"User: {current_user}")
        logger.debug(f"Handling request: {request}")
        if self._next:
            logger.debug(f"Passing request to next handler: {self._next}")
            return await self._next.handle(request, db, current_user, ldap_service)
        return "No handler could process the request."

# ----------------------------------------------------------------------------------------
# IT HANDLER
# ----------------------------------------------------------------------------------------
class ITHandler(Handler):
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser,
        ldap_service: LDAPService
    ) -> ApprovalRequest:
        approver_policy = ApproverPolicy(current_user)
        
        logger.debug(f"User: {current_user.groups}")
        # IT can only approve requests from fund 511***
        logger.debug("IT HANDLER PROCESSING REQUEST")
        
        # Query the assigned_group column in pending_approvals table
        assigned_group = await dbas.get_assigned_group(db, request.uuid)
        
        if approver_policy.can_it_approve(request.fund, ItemStatus.NEW_REQUEST):
            # IT can approve IT-related requests
            logger.debug(f"IT HANDLER APPROVING IT REQUEST: {request.uuid}")
	
            # Get the approval UUID and task_id for this line item
            stmt = select(dbas.Approval.UUID, dbas.PendingApproval.pending_approval_id).join(
                dbas.PendingApproval,
                dbas.PendingApproval.approvals_uuid == dbas.Approval.UUID
            ).where(
                dbas.PendingApproval.line_item_uuid == request.uuid
            )
            result = await db.execute(stmt)
            row = result.first()
            
            if row:
                approvals_uuid, pending_approval_id = row
                # --------------------------------------------------------
                # Use the insert_final_approval function
                await dbas.insert_final_approval(
                    db=db,
                    approvals_uuid=approvals_uuid,
                    purchase_request_id=request.id,
                    line_item_uuid=request.uuid,
                    pending_approval_id=pending_approval_id,
                    approver=request.approver,
                    status=ItemStatus.PENDING_APPROVAL,
                    deputy_can_approve=dbas.can_deputy_approve(request.total_price)
                )
                
                # Send email to clerk admins requesting approval
                logger.debug(f"IT HANDLER: Sending email to clerk admins requesting approval for {request.uuid}")
                
                """
                Send to the correct approver handler, the new request has been approved so we need to ensure the correct
                approver is notified, lets test for deputy clerk first
                """
                
                logger.debug(f"REQUEST: {request}")
                logger.debug(f"CURRENT USER: {current_user}")
                logger.debug(f"LDAP SERVICE: {ldap_service}")
                
                approver_email_builder = ApproverEmailBuilder(db, request, current_user, ldap_service)
                email_payload = await approver_email_builder.build_email_payload()
                await smtp_service.send_approver_email(email_payload,db=db)
                
                logger.debug(f"IT HANDLER: Inserted final approval for {request.uuid}")
            else:
                logger.error(f"IT HANDLER: Could not find approval/task data for {request.uuid}")
        
        return await super().handle(request, db, current_user, ldap_service)

# ----------------------------------------------------------------------------------------
# FINANCE HANDLER
# ----------------------------------------------------------------------------------------
class FinanceHandler(Handler):
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser,
        ldap_service: LDAPService
    ) -> ApprovalRequest:
        approver_policy = ApproverPolicy(current_user)
        
        logger.debug(f"User: {current_user}")
        # Finance can approve any request that doesn't start with 511
        logger.debug("FINANCE HANDLER PROCESSING REQUEST")
        
        if approver_policy.can_finance_approve(request.fund, ItemStatus.NEW_REQUEST):
            # Finance handles non-IT requests
            logger.debug(f"FINANCE HANDLER APPROVING NON-IT REQUEST: {request.uuid}")
            
            # Get the approval UUID and task_id for this line item
            stmt = select(dbas.Approval.UUID, dbas.PendingApproval.pending_approval_id).join(
                dbas.PendingApproval,
                dbas.PendingApproval.approvals_uuid == dbas.Approval.UUID
            ).where(
                dbas.PendingApproval.line_item_uuid == request.uuid
            )
            result = await db.execute(stmt)
            row = result.first()
            logger.debug(f"FINANCE HANDLER: Row: {row}")
            
            if row:
                approvals_uuid, pending_approval_id = row
                
                # Use the insert_final_approval function, this is just a table, its not making it final approved
                await dbas.insert_final_approval(
                    db=db,
                    approvals_uuid=approvals_uuid,
                    purchase_request_id=request.id,
                    line_item_uuid=request.uuid,
                    pending_approval_id=pending_approval_id,
                    approver=request.approver,
                    status=ItemStatus.PENDING_APPROVAL,
                    deputy_can_approve=dbas.can_deputy_approve(request.total_price)
                )
                
                # Send email to clerk admins requesting approval
                logger.debug(f"FINANCE HANDLER: Sending email to clerk admins requesting approval for {request.uuid}")
                approver_email_builder = ApproverEmailBuilder(db, request, current_user, ldap_service)
                email_payload = await approver_email_builder.build_email_payload()
                await smtp_service.send_approver_email(email_payload,db=db)
                
                logger.debug(f"FINANCE HANDLER: Inserted final approval for {request.uuid}")
            else:
                logger.error(f"FINANCE HANDLER: Could not find approval/task data for {request.uuid}")
        
        return await super().handle(request, db, current_user, ldap_service)
    
###############################################################################################
# CLERK ADMIN HANDLER
###############################################################################################
class ClerkAdminHandler(Handler):
    def __init__(self):
        self._next: Optional[Handler] = None
        
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser,
        ldap_service: LDAPService
    ) -> ApprovalRequest:
        
        approver_policy = ApproverPolicy(current_user)
        
        # ClerkAdmin is the final handler - they can approve based on price
        logger.debug("CLERK ADMIN HANDLER PROCESSING REQUEST")
        
        # Get current status from pending_approvals table
        stmt = select(dbas.PendingApproval.status).where(dbas.PendingApproval.line_item_uuid == request.uuid)
        result = await db.execute(stmt)		
        row = result.first()
        
        if not row:
            logger.warning(f"CLERK ADMIN HANDLER: No pending approval found for {request.uuid}")
            return await super().handle(request, db, current_user, ldap_service)
            
        current_status = row[0]
        logger.debug(f"CURRENT STATUS: {current_status}")
        
        # ClerkAdmin should only process requests that are already in PENDING_APPROVAL
        can_approve = await approver_policy.can_clerk_admin_approve(
            request.total_price,
            current_status,
            request,
            db
        )
        
        if not can_approve:
            logger.debug(f"CLERK ADMIN HANDLER: {current_user.username} cannot approve request {request.uuid}")
            return request
        
        # Get the approval UUID for this line item
        stmt = select(dbas.Approval.UUID).join(
            dbas.PendingApproval,
            dbas.PendingApproval.approvals_uuid == dbas.Approval.UUID
        ).where(
            dbas.PendingApproval.line_item_uuid == request.uuid
        )
        result = await db.execute(stmt)
        row = result.first()

        if not row:
            logger.error(f"CLERK ADMIN HANDLER: Could not find approval UUID for {request.uuid}")
            return await super().handle(request, db, current_user, ldap_service)
            
        approvals_uuid = row[0]
        
        # Mark request as APPROVED
        await dbas.mark_final_approval_as_approved(db, approvals_uuid)
            
        # Send email to requester that their request has been approved
        logger.debug(f"CLERK ADMIN HANDLER: Sending email to requester that their request has been approved for {request.uuid}")
        
        approver_email_builder = ApproverEmailBuilder(db, request, current_user, ldap_service)
        email_payload = await approver_email_builder.build_email_payload()
        await smtp_service.send_request_approved_email(email_payload,db=db)
        logger.debug(f"CLERK ADMIN HANDLER: Inserted final approval for {request.uuid}")
        
        # Pass the request to the next handler
        if self._next:
            return await self._next.handle(request, db, current_user, ldap_service)
        return request