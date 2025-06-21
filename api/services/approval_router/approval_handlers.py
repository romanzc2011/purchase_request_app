from __future__ import annotations
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from loguru import logger
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
import api.services.db_service as dbas

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
    def handle(self, request: ApprovalRequest) -> ApprovalRequest:
        logger.info(f"Handling request: {request}")
        if self._next:
            logger.info(f"Passing request to next handler: {self._next}")
            return self._next.handle(request)
        return "No handler could process the request."
    
class ITHandler(Handler):
    def handle(self, request: ApprovalRequest) -> ApprovalRequest:
        # IT can only approve requests from fund 511***
        logger.info("Assigned group was handled in db but this is IT Handler")

            
            # Update the Approval Table to Pending Approval
            #dbas.update_data_by_uuid(request.uuid, "approvals", status=ItemStatus.PENDING_APPROVAL)
	
		# Send email to final approvers (Ted and Edmund) and CC finance department (Roman for testing)
        return super().handle(request)
    
class FinanceHandler(Handler):
    def handle(self, request: ApprovalRequest) -> ApprovalRequest:
        # Finance can approve any request
        logger.info("Assigned group was handled in db but this is Finance Handler")
        return super().handle(request)
    
class ClerkAdminHandler(Handler):
    def __init__(self):
        self._next: Optional[Handler] = FinanceHandler()
    def handle(self, request: ApprovalRequest) -> ApprovalRequest:
        # This variable determines if Edmund can approve the request
        if request.total_price < 250:
            edmund_can_approve = True