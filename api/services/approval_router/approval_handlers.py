from __future__ import annotations
import asyncio
from typing import Optional
from abc import ABC, abstractmethod
from api.schemas.enums import AssignedGroup, CueClerk
from api.dependencies.pras_dependencies import smtp_service
from api.services.approval_router.approval_utils import ApprovalUtils
from api.services.progress_tracker.progress_manager import get_active_tracker, get_approval_tracker
from api.services.progress_tracker.progress_tracker import ProgressTrackerType
from api.services.progress_tracker.steps.approval_steps import ApprovalStepName
from api.utils.misc_utils import format_username
from api.utils.logging_utils import logger_init_ok
from loguru import logger
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
import api.services.db_service as dbas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.schemas.ldap_schema import LDAPUser
from api.services.approval_router.approver_policy import ApproverPolicy
from api.services.smtp_service.email_builder import ApproverEmailBuilder
from api.services.ldap_service import LDAPService
from api.utils.misc_utils import reset_signals
from api.services.ipc_status import ipc_status
import api.services.socketio_server.sio_events as sio_events


# Approval Router to determine the routing of requests
class Handler(ABC):
    def __init__(self):
        logger.info(f"Handler initialized")
        self._next: Optional["Handler"] = None
        tracker = get_active_tracker()
        
        # Init local trackers to prevent error
        approval_tracker = None

        # Get download tracker
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
        
        if approval_tracker:
            approval_tracker.mark_step_done(ApprovalStepName.HANDLER_BASE_INITIALIZED)
            logger_init_ok("Handler base initialized")
        
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
        
        if self._next:
            return await self._next.handle(request, db, current_user, ldap_service)
        
        # Reset progress bar/signals, everything
        reset_signals()
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
        policy = ApproverPolicy(current_user)
        
        sid = sio_events.get_user_sid(current_user)
        
        # Mark IT handler initialized
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.IT_HANDLER_INITIALIZED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
        
        if policy.can_it_approve(request.fund, ItemStatus.NEW_REQUEST):
            logger.debug("IT HANDLER CAN APPROVE HANDLER")
            
            row = await ApprovalUtils.get_approval_data(db, request.uuid)
            
            if not row:
                logger.error(f"IT HANDLER: Could not find approval/task data for {request.uuid}")
                return await super().handle(request, db, current_user, ldap_service)
            
            approvals_uuid, pending_approval_id = row
            await ApprovalUtils.insert_pending_approval(db, approvals_uuid, request, pending_approval_id)
            
            # Set IPC status flags for IT requests (same as Management requests)
            if request.status is ItemStatus.PENDING_APPROVAL:
                await ipc_status.update(field="request_pending", value=True)
                await ipc_status.update(field="approval_email_sent", value=True) # Just make sure set to True to complete progress bar
                
            elif request.status is ItemStatus.APPROVED:
                await ipc_status.update(field="request_approved", value=True)
            
            await ApprovalUtils.build_and_send_email(
                group=AssignedGroup.IT.value,
                db=db,
                request=request,
                current_user=current_user,
                ldap_service=ldap_service
            )
        
        # Mark IT approval processed (even if not approved, the step is complete)
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.IT_APPROVAL_PROCESSED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
            
        return await super().handle(request, db, current_user, ldap_service)
# ----------------------------------------------------------------------------------------
# MANAGEMENT HANDLER
# ----------------------------------------------------------------------------------------
class ManagementHandler(Handler):
    """
    The route of the non-IT (092x) requests is as follows:
    - Request is sent to management: Edmund/Lelaxz
    - If the value <= $250 then Edmund may go ahead and approve
    - If the value is > $250 then Edmund can do a PENDING APPROVAL that gets sent to Ted
    - Ted will deny/approve 
    """
    async def handle(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser,
        ldap_service: LDAPService
    ) -> ApprovalRequest:
        #!----------------------------------------------------------
        #! TEST USER OVERRIDE - REMOVED FOR PRODUCTION
        #!----------------------------------------------------------
        
        approver_policy = ApproverPolicy(current_user)
        sid = sio_events.get_user_sid(current_user)
        
        # Management can approve any request that doesn't start with 511
        logger.debug("MANAGEMENT HANDLER PROCESSING REQUEST")
        
        # Mark Management handler initialized
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.MANAGEMENT_HANDLER_INITIALIZED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
        
        """
        Finance/Management 092x will email TO: Edmund Brown, Lela
        CC Peter, Lauren
        """
        #? Determine whether MANAGEMENT can approve, ie Edmund value <= $250
        if approver_policy.can_management_approve(request.fund, ItemStatus.NEW_REQUEST):
            # Management handles non-IT requests
            logger.debug(f"MANAGEMENT HANDLER APPROVING NON-IT REQUEST: {request.uuid}")
            
            # Get the approval UUID and task_id for this line item
            stmt = select(dbas.Approval.UUID, dbas.PendingApproval.pending_approval_id).join(
                dbas.PendingApproval,
                dbas.PendingApproval.approvals_uuid == dbas.Approval.UUID
            ).where(
                dbas.PendingApproval.line_item_uuid == request.uuid
            )
            result = await db.execute(stmt)
            row = result.first()
            logger.debug(f"MANAGEMENT HANDLER: Row: {row}")
            
            if row:
                approvals_uuid, pending_approval_id = row
                
                # Initialize variables
                pending_approved_by = None
                final_approved_by = None
                pending_approved_at = None
                final_approved_at = None
                
                if request.status is ItemStatus.PENDING_APPROVAL:
                    pending_approved_by = format_username(request.approver)
                    pending_approved_at = dbas.utc_now_truncated()
                    await ipc_status.update(field="request_pending", value=True)
                
                if request.status is ItemStatus.APPROVED:
                    final_approved_by = format_username(request.approver)
                    final_approved_at = dbas.utc_now_truncated()
                    await ipc_status.update(field="request_approved", value=True)
                    
                # Use the insert_final_approval function, this is just a table, its not making it final approved
                await dbas.insert_final_approval(
                    db=db,
                    approvals_uuid=approvals_uuid,
                    purchase_request_id=request.id,
                    line_item_uuid=request.uuid,
                    pending_approval_id=pending_approval_id,
                    status=ItemStatus.PENDING_APPROVAL,
                    deputy_can_approve=dbas.can_deputy_approve(request.total_price),
                    pending_approved_by=pending_approved_by,
                    final_approved_by=final_approved_by,
                    pending_approved_at=pending_approved_at,
                    final_approved_at=final_approved_at
                )
                
                # Send email to clerk admin and management (Edmund/Lela) requesting approval
                logger.debug(f"MANAGEMENT HANDLER: Sending email to clerk admins requesting approval for {request.uuid}")
                approver_email_builder = ApproverEmailBuilder(db, request, current_user, ldap_service)
                email_payload = await approver_email_builder.build_email_payload()
                
                await smtp_service.send_approver_email(email_payload, db=db, send_to=AssignedGroup.MANAGEMENT.value)
                await ipc_status.update(field="approval_email_sent", value=True)
                logger.debug(f"MANAGEMENT HANDLER: Inserted final approval for {request.uuid}")
                
                # Mark Management approval processed
                tracker = get_active_tracker()
                if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
                    approval_tracker = get_approval_tracker()
                    step_data = approval_tracker.mark_step_done(ApprovalStepName.MANAGEMENT_APPROVAL_PROCESSED)
                    if sid and step_data:
                        await sio_events.progress_update(sid, step_data)
            else:
                logger.error(f"MANAGEMENT HANDLER: Could not find approval/task data for {request.uuid}")
        
        # Mark Management approval processed (even if not approved, the step is complete)
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.MANAGEMENT_APPROVAL_PROCESSED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
            
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
        
        # ClerkAdmin is the final handler - they can approve based on price
        logger.critical("CLERK ADMIN HANDLER PROCESSING REQUEST")
        
        sid = sio_events.get_user_sid(current_user)
        
        # Mark Clerk Admin handler initialized
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.CLERK_ADMIN_HANDLER_INITIALIZED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
            else:
                logger.error(f"CLERK ADMIN HANDLER: Could not mark step done for {ApprovalStepName.CLERK_ADMIN_HANDLER_INITIALIZED}")
        approver_policy = ApproverPolicy(current_user)    # Create an instance of the approver policy
        
        # Get current status from pending_approvals table
        stmt = select(dbas.PendingApproval.status).where(dbas.PendingApproval.line_item_uuid == request.uuid)
        result = await db.execute(stmt)		
        row = result.first()
        
        if not row:
            logger.warning(f"CLERK ADMIN HANDLER: No pending approval found for {request.uuid}")
            return await super().handle(request, db, current_user, ldap_service)
        
        current_status = row[0]
        logger.debug(f"CURRENT STATUS: {current_status}")
        
        logger.debug("CLERK ADMIN HANDLER PROCESSING REQUEST")
        can_approve_now = await approver_policy.can_fully_approve(
            total_price=request.total_price,
            current_status=current_status,
            db=db
        )
        logger.warning(f"CAN APPROVE NOW: {can_approve_now}")
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        # Mark Clerk policy checked
        sid = sio_events.get_user_sid(current_user)
        
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.CLERK_POLICY_CHECKED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
            else:
                logger.error(f"CLERK ADMIN HANDLER: Could not mark step done for {ApprovalStepName.CLERK_POLICY_CHECKED}")
            
        if not can_approve_now:
            logger.debug("CLERK ADMIN HANDLER: Current user is not allowed to approve this request")
            
            approver_email_builder = ApproverEmailBuilder(db, request, current_user, ldap_service)
            email_payload = await approver_email_builder.build_email_payload()
            
            await smtp_service.send_approver_email(
                email_payload, 
                db=db, 
                send_to=[AssignedGroup.DEPUTY_CLERK.value, AssignedGroup.CHIEF_CLERK.value])
            
            # Mark clerk approval processed (even if not approved, the step is complete)
            #!-PROGRESS TRACKING --------------------------------------------------------------
            tracker = get_active_tracker()
            if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
                approval_tracker = get_approval_tracker()
                step_data = approval_tracker.mark_step_done(ApprovalStepName.CLERK_APPROVAL_PROCESSED)
                if sid and step_data:
                    await sio_events.progress_update(sid, step_data)
                else:
                    logger.error(f"CLERK ADMIN HANDLER: Could not mark step done for {ApprovalStepName.CLERK_APPROVAL_PROCESSED}")
                return await super().handle(request, db, current_user, ldap_service)
        
        #*#################################################################################
        #*#################################################################################
        # * Code below is for if the request was approved
        #*#################################################################################
        #*#################################################################################
        logger.debug("PROCESS APPROVAL")
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
        logger.debug(f"APPROVAL UUID RETRIEVED: {approvals_uuid}")
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        # Mark approval UUID retrieved
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.APPROVAL_UUID_RETRIEVED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
            else:
                logger.error(f"CLERK ADMIN HANDLER: Could not mark step done for {ApprovalStepName.APPROVAL_UUID_RETRIEVED}")
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        # Mark request as APPROVED
        logger.debug("MARKING FINAL APPROVAL AS APPROVED")
        
        sid = sio_events.get_user_sid(current_user)
        await dbas.mark_final_approval_as_approved(db, approvals_uuid)
        
        row = await ApprovalUtils.get_approval_data(db, request.uuid)
            
        if not row:
            logger.error(f"CLERK ADMIN HANDLER: Could not find approval/task data for {request.uuid}")
            return await super().handle(request, db, current_user, ldap_service)
            
        approvals_uuid, pending_approval_id = row
        await dbas.update_final_approval_status(
            db=db,
            approvals_uuid=approvals_uuid,
            line_item_uuid=request.uuid,
            pending_approval_id=pending_approval_id,
            status=ItemStatus.APPROVED,
            final_approved_by=current_user.username,
            final_approved_at=dbas.utc_now_truncated()
        )
        
        logger.debug(f"FINAL APPROVAL MARKED AS APPROVED: {approvals_uuid}, {request.uuid}, {pending_approval_id}")
        logger.debug("FINAL APPROVAL MARKED AS APPROVED")
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        # Mark request marked approved
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.REQUEST_MARKED_APPROVED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
            else:
                logger.error(f"CLERK ADMIN HANDLER: Could not mark step done for {ApprovalStepName.REQUEST_MARKED_APPROVED}")
            
        # Send email to requester that their request has been approved
        logger.debug(f"CLERK ADMIN HANDLER: Sending email to requester that their request has been approved for {request.uuid}")
        
        logger.debug("BUILDING EMAIL PAYLOAD")
        approver_email_builder = ApproverEmailBuilder(db, request, current_user, ldap_service)
        email_payload = await approver_email_builder.build_email_payload()
        logger.debug("EMAIL PAYLOAD BUILT")
        
        logger.debug("SENDING REQUEST APPROVED EMAIL")
        await smtp_service.send_request_approved_email(email_payload,db=db)
        logger.debug("REQUEST APPROVED EMAIL SENT")
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        # Mark approval email sent
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.APPROVAL_EMAIL_SENT)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
            else:
                logger.error(f"CLERK ADMIN HANDLER: Could not mark step done for {ApprovalStepName.APPROVAL_EMAIL_SENT}")
            
        logger.debug(f"CLERK ADMIN HANDLER: Inserted final approval for {request.uuid}")
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        # Mark clerk approval processed
        tracker = get_active_tracker()
        if tracker and tracker.active_tracker == ProgressTrackerType.APPROVAL:
            approval_tracker = get_approval_tracker()
            step_data = approval_tracker.mark_step_done(ApprovalStepName.CLERK_APPROVAL_PROCESSED)
            if sid and step_data:
                await sio_events.progress_update(sid, step_data)
            else:
                logger.error(f"CLERK ADMIN HANDLER: Could not mark step done for {ApprovalStepName.CLERK_APPROVAL_PROCESSED}")
        
        # Pass the request to the next handler
        if self._next:
            return await self._next.handle(request, db, current_user, ldap_service)
        return request