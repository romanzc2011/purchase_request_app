from __future__ import annotations
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from loguru import logger
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest, PendingApprovalCreate as PendingApproval
from api.services.database_service import DatabaseService as dbas

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
    def handle(self, request: PendingApproval) -> PendingApproval:
        logger.info(f"Handling request: {request}")
        if self._next:
            logger.info(f"Passing request to next handler: {self._next}")
            return self._next.handle(request)
        return "No handler could process the request."
    
class ITHandler(Handler):
    def handle(self, request: PendingApproval) -> PendingApproval:
        # IT can only approve requests from fund 511***
        logger.info(f"ITHandler: Checking if request is from fund 511*** and status is NEW_REQUEST")
        if request.fund.startswith("511") and request.status == ItemStatus.NEW_REQUEST:
            logger.info(f"ITHandler: Request is from fund 511*** and status is NEW_REQUEST")
            request.status = ItemStatus.PENDING_APPROVAL
            logger.info(f"ITHandler: Request status updated to {request.status}")
            
            # Update the Approval Table to Pending Approval
            dbas.update_data_by_uuid(request.uuid, "approvals", status=ItemStatus.PENDING_APPROVAL)
            
            # Send email to final approvers (Ted and Edmund) and CC finance department (Roman for testing)
            
            pass
            # Update approval tables status
            pass
        
            logger.info(f"IT approved request {request.id}, forward to clerk admin for final approval")
            return super().handle(request)
        # Send to finance department
        return super().handle(request)
    
class FinanceHandler(Handler):
    def handle(self, request: PendingApproval) -> PendingApproval:
        # Finance can approve any request
        if request.status == ItemStatus.NEW_REQUEST and not request.fund.startswith("511"):
            request.status = ItemStatus.PENDING_APPROVAL
            
            # Send email to final approvers (Ted and Edmund) and CC finance department
            pass
            
            # Update approval tables status
            pass
            logger.info(f"Finance approved request {request.id}")
            return super().handle(request)
        # Send to clerk admin
        return super().handle(request)
    
class ClerkAdminHandler(Handler):
    def __init__(self):
        self._next: Optional[Handler] = FinanceHandler()
    def handle(self, request: PendingApproval) -> PendingApproval:
        # This variable determines if Edmund can approve the request
        if request.total_price < 250:
            edmund_can_approve = True