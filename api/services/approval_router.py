from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
from loguru import logger
from api.schemas.pydantic_schemas import ItemStatus
from api.services.database_service import DatabaseService as dbas

# Approval Router to determine the routing of requests

@dataclass
class ApprovalRequest:
    """
    ApprovalRequest is responsible for determining the routing of requests
    based on the fund and the status of the request.
    """
    lawb_id: str
    uuid: str
    fund: str
    total_price: float
    status: str = ItemStatus.NEW_REQUEST
    metadata: dict = None
    
class Handler:
    def __init__(self):
        self._next: Optional[Handler] = None
        
    def set_next(self, handler: Handler) -> Handler:
        self._next = handler
        return handler

    def handle(self, request: ApprovalRequest) -> ApprovalRequest:
        if self._next:
            return self._next.handle(request)
        return request
    
class ITHandler(Handler):
    def handle(self, request: ApprovalRequest) -> ApprovalRequest:
        # IT can only approve requests from fund 511***
        if request.fund.startswith("511") and request.status == ItemStatus.NEW_REQUEST:
            request.status = ItemStatus.PENDING_APPROVAL
            
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
    def handle(self, request: ApprovalRequest) -> ApprovalRequest:
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
    def handle(self, request: ApprovalRequest) -> ApprovalRequest:
        # This variable determines if Edmund can approve the request
        if request.total_price < 250:
            edmund_can_approve = True