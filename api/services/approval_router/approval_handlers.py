from __future__ import annotations
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from loguru import logger
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
import api.services.db_service as dbas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
    async def handle(self, request: ApprovalRequest, db: AsyncSession) -> ApprovalRequest:
        logger.info(f"Handling request: {request}")
        if self._next:
            logger.info(f"Passing request to next handler: {self._next}")
            return await self._next.handle(request, db)
        return "No handler could process the request."

# ----------------------------------------------------------------------------------------
# IT HANDLER
# ----------------------------------------------------------------------------------------
class ITHandler(Handler):
    async def handle(self, request: ApprovalRequest, db: AsyncSession) -> ApprovalRequest:
        # IT can only approve requests from fund 511***
        logger.info("IT Handler processing request")
        
        if request.fund.startswith("511"):
            # IT can approve IT-related requests
            logger.info(f"IT Handler approving IT request: {request.uuid}")
            
            # Get the approval UUID and task_id for this line item
            stmt = select(dbas.Approval.UUID, dbas.PendingApproval.task_id).join(
                dbas.PendingApproval,
                dbas.PendingApproval.approvals_uuid == dbas.Approval.UUID
            ).where(
                dbas.PendingApproval.line_item_uuid == request.uuid
            )
            result = await db.execute(stmt)
            row = result.first()
            
            if row:
                approvals_uuid, task_id = row
                
                # Use the insert_final_approval function
                await dbas.insert_final_approval(
                    db=db,
                    approvals_uuid=approvals_uuid,
                    line_item_uuid=request.uuid,
                    task_id=task_id,
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
                
                logger.info(f"IT Handler: Inserted final approval for {request.uuid}")
            else:
                logger.error(f"IT Handler: Could not find approval/task data for {request.uuid}")
        
        return await super().handle(request, db)
    
class FinanceHandler(Handler):
    async def handle(self, request: ApprovalRequest, db: AsyncSession) -> ApprovalRequest:
        # Finance can approve any request that doesn't start with 511
        logger.info("Finance Handler processing request")
        
        if not request.fund.startswith("511"):
            # Finance handles non-IT requests
            logger.info(f"Finance Handler approving non-IT request: {request.uuid}")
            
            # Get the approval UUID and task_id for this line item
            stmt = select(dbas.Approval.UUID, dbas.PendingApproval.task_id).join(
                dbas.PendingApproval,
                dbas.PendingApproval.approvals_uuid == dbas.Approval.UUID
            ).where(
                dbas.PendingApproval.line_item_uuid == request.uuid
            )
            result = await db.execute(stmt)
            row = result.first()
            logger.info(f"Finance Handler: Row: {row}")
            
            if row:
                approvals_uuid, task_id = row
                
                # Use the insert_final_approval function
                await dbas.insert_final_approval(
                    db=db,
                    approvals_uuid=approvals_uuid,
                    line_item_uuid=request.uuid,
                    task_id=task_id,
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
        
        return await super().handle(request, db)
    
class ClerkAdminHandler(Handler):
    def __init__(self):
        self._next: Optional[Handler] = None
        
    async def handle(self, request: ApprovalRequest, db: AsyncSession) -> ApprovalRequest:
        # ClerkAdmin is the final handler - they can approve based on price
        logger.info("ClerkAdmin Handler processing request")
        
        # This variable determines if Edmund can approve the request
        if request.total_price < 250:
            edmund_can_approve = True
            logger.info("ClerkAdmin Handler: Edmund can approve (price < $250)")
        else:
            edmund_can_approve = False
            logger.info("ClerkAdmin Handler: Edmund cannot approve (price >= $250)")
        
        # Only insert if this is a final approval (price < $250) or if no other handler has processed it
        # For now, let's just log the deputy approval status
        logger.info(f"ClerkAdmin Handler: Deputy can approve: {edmund_can_approve} for request {request.uuid}")
        
        if self._next:
            return await self._next.handle(request, db)
        return request