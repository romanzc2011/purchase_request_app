from __future__ import annotations
from typing import Optional
from dataclasses import dataclass

# Approval Router to determine the routing of requests

@dataclass
class ApprovalRequest:
    """
    ApprovalRequest is responsible for determining the routing of requests
    based on the fund and the status of the request.
    """
    id: str
    uuid: str
    fund: str
    total_price: float
    status: str = "NEW REQUEST"
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
        if request.fund.startswith("511"):
            request.status = "PENDING APPROVAL"
            logger.info(f"IT approved request {request.id}, forward to clerk admin for final approval")
            return super().handle(request)
        return super().handle(request)