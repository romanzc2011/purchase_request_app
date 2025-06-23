from __future__ import annotations
import asyncio
from http.client import HTTPException
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from api import settings
from api.schemas.email_schemas import EmailPayloadRequest, LineItemsPayload
from api.services import cache_service, smtp_service
from loguru import logger
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
import api.services.db_service as dbas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from api.schemas.ldap_schema import LDAPUser

# Approval Router to determine the routing of requests
class Handler(ABC):
    def __init__(self):
        logger.info(f"Handler initialized")
        self._next = None
        
    def set_next(self, handler: "Handler") -> "Handler":
        logger.info(f"Setting next handler: {handler}")
        self._next = handler
        return handler
    
    @abstractmethod
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser
    ) -> ApprovalRequest:
        
        logger.debug(f"User: {current_user}")
        logger.info(f"Handling request: {request}")
        if self._next:
            logger.info(f"Passing request to next handler: {self._next}")
            return await self._next.handle(request, db, current_user)
        return "No handler could process the request."

# ----------------------------------------------------------------------------------------
# IT HANDLER
# ----------------------------------------------------------------------------------------
class ITHandler(Handler):
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser
    ) -> ApprovalRequest:
        
        logger.debug(f"User: {current_user.groups}")
        # IT can only approve requests from fund 511***
        logger.info("IT Handler processing request")
        
        # Query the assigned_group column in pending_approvals table
        assigned_group = await dbas.get_assigned_group(db, request.uuid)
        
        if assigned_group == "IT":
            # IT can approve IT-related requests
            logger.info(f"IT Handler approving IT request: {request.uuid}")
	
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
                    line_item_uuid=request.uuid,
                    pending_approval_id=pending_approval_id,
                    approver=request.approver,
                    status=request.status,
                    approval_status=ItemStatus.PENDING_APPROVAL,
                    deputy_can_approve=dbas.can_deputy_approve(request.total_price)
                )
                
                #################################################################################
                ## BUILD EMAIL PAYLOADS
                #################################################################################
                # Get additional comments
                additional_comments = cache_service.get_or_set(
                    "comments",
                    request.id,
                    lambda: dbas.get_additional_comments_by_id(request.id)
                )

                for item in request.items:
                    item.additional_comments = additional_comments
                
                items_for_email = [
                    LineItemsPayload(
                        budgetObjCode=item.budget_obj_code,
                        itemDescription=item.item_description,
                        location=item.location,
                        justification=item.justification,
                        quantity=item.quantity,
                        priceEach=item.price_each,
                        totalPrice=item.total_price,
                        fund=item.fund
                    )
                    for item in request.items
                ]
                # --------------------------------------------------------
                # Send notification to final_approvers that they have a request to approve/deny
                email_request_payload = EmailPayloadRequest(
                    model_type="email_request",
                    ID=request.id,
                    requester=request.requester,
                    requester_email=request.requester_email,
                    datereq=request.items[0].datereq,
                    dateneed=request.items[0].dateneed,
                    orderType=request.items[0].order_type,
                    subject=f"Purchase Request #{request.id}",
                    sender=settings.smtp_email_addr,
                    to=None,   # Assign this in the smtp service
                    cc=None,
                    bcc=None,
                    text_body=None,
                    approval_link=f"{settings.link_to_request}",
                    items=items_for_email,
                    attachments=[pdf_path, *uploaded_files]
                )
                
                """
                # Make the to a condition, if this is a request from a requester, then we need to send it to the approvers
                # But we need to also send a confirmation to requester that is has been sent to the approvers
                """

                logger.info(f"EMAIL PAYLOAD REQUEST: {email_request_payload}")
                
                # Notify requester and approvers
                logger.info("Notifying requester and approvers")
                
                # Send request to approvers and requester
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(smtp_service.send_approver_email(email_request_payload))
                
                logger.info(f"IT Handler: Inserted final approval for {request.uuid}")
            else:
                logger.error(f"IT Handler: Could not find approval/task data for {request.uuid}")
        
        return await super().handle(request, db, current_user)
    
class FinanceHandler(Handler):
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser
    ) -> ApprovalRequest:
        
        logger.debug(f"User: {current_user}")
        # Finance can approve any request that doesn't start with 511
        logger.info("Finance Handler processing request")
        
        if not request.fund.startswith("511"):
            # Finance handles non-IT requests
            logger.info(f"Finance Handler approving non-IT request: {request.uuid}")
            
            # Get the approval UUID and task_id for this line item
            stmt = select(dbas.Approval.UUID, dbas.PendingApproval.pending_approval_id).join(
                dbas.PendingApproval,
                dbas.PendingApproval.approvals_uuid == dbas.Approval.UUID
            ).where(
                dbas.PendingApproval.line_item_uuid == request.uuid
            )
            result = await db.execute(stmt)
            row = result.first()
            logger.info(f"Finance Handler: Row: {row}")
            
            if row:
                approvals_uuid, pending_approval_id = row
                
                # Use the insert_final_approval function, this is just a table, its not making it final approved
                await dbas.insert_final_approval(
                    db=db,
                    approvals_uuid=approvals_uuid,
                    line_item_uuid=request.uuid,
                    pending_approval_id=pending_approval_id,
                    approver=request.approver,
                    status=request.status,
                    pending_approval_status=ItemStatus.PENDING_APPROVAL,
                    deputy_can_approve=dbas.can_deputy_approve(request.total_price)
                )
                
                # Update status in different tables using their correct primary keys
                # Update pr_line_items using line_item_uuid
                await dbas.update_status_by_uuid(
                    db=db,
                    uuid=request.uuid,  # line_item_uuid
                    status=ItemStatus.PENDING_APPROVAL,
                    table="pr_line_items"
                )
                
                # Update approvals using approvals_uuid
                await dbas.update_status_by_uuid(
                    db=db,
                    uuid=approvals_uuid,
                    status=ItemStatus.PENDING_APPROVAL,
                    table="approvals"
                )
                
                # Update pending_approvals using approvals_uuid
                await dbas.update_status_by_uuid(
                    db=db,
                    uuid=approvals_uuid,
                    status=ItemStatus.PENDING_APPROVAL,
                    table="pending_approvals"
                )
                
                logger.info(f"Finance Handler: Inserted final approval for {request.uuid}")
            else:
                logger.error(f"Finance Handler: Could not find approval/task data for {request.uuid}")
        
        return await super().handle(request, db, current_user)
    
class ClerkAdminHandler(Handler):
    def __init__(self):
        self._next: Optional[Handler] = None
        
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser
    ) -> ApprovalRequest:
        
        # ClerkAdmin is the final handler - they can approve based on price
        logger.info("ClerkAdmin Handler processing request")
        
        # Get current status from pending_approvals table
        stmt = select(dbas.PendingApproval.task_status).where(dbas.PendingApproval.line_item_uuid == request.uuid)
        result = await db.execute(stmt)
        row = result.first()
        
        if not row:
            logger.warning(f"ClerkAdmin Handler: No pending approval found for {request.uuid}")
            return await super().handle(request, db, current_user)
            
        current_status = row[0]
        logger.info(f"CURRENT STATUS: {current_status}")
        
        # ClerkAdmin should only process requests that are already in PENDING_APPROVAL
        if current_status != ItemStatus.PENDING_APPROVAL:
            logger.info(f"ClerkAdmin Handler: Request {request.uuid} is not in PENDING_APPROVAL status ({current_status}), skipping")
            return await super().handle(request, db, current_user)
        
        # Ensure user is in the CUE group
        if "CUE_GROUP" not in current_user.groups:
            logger.warning(f"User {current_user.username} is not in the CUE group")
            raise HTTPException(status_code=403, detail="User is not in the CUE group")
        
        # This variable determines if Edmund can approve the request
        if request.total_price < 250:
            edmund_can_approve = True
            logger.info("ClerkAdmin Handler: Edmund can approve (price < $250)")
        else:
            edmund_can_approve = False
            logger.info("ClerkAdmin Handler: Edmund cannot approve (price >= $250)")
            
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
            logger.error(f"ClerkAdmin Handler: Could not find approval UUID for {request.uuid}")
            return await super().handle(request, db, current_user)
            
        approvals_uuid = row[0]
        
        # Update all statuses to APPROVED
        # Update pr_line_items using line_item_uuid
        await dbas.update_status_by_uuid(
            db=db,
            uuid=request.uuid,  # line_item_uuid
            status=ItemStatus.APPROVED,
            table="pr_line_items"
        )
        
        # Update approvals using approvals_uuid
        await dbas.update_status_by_uuid(
            db=db,
            uuid=approvals_uuid,
            status=ItemStatus.APPROVED,
            table="approvals"
        )
        
        # Update pending_approvals using approvals_uuid
        await dbas.update_status_by_uuid(
            db=db,
            uuid=approvals_uuid,
            status=ItemStatus.APPROVED,
            table="pending_approvals"
        )
        
        #TODO: Send email to requester that their request has been approved
        
        logger.info(f"ClerkAdmin Handler: Deputy can approve: {edmund_can_approve} for request {request.uuid}")
        
        if self._next:
            return await self._next.handle(request, db, current_user)
        return request