from api.services.approval_router.approval_handlers import ITHandler, FinanceHandler, ClerkAdminHandler
from api.schemas.approval_schemas import ApprovalRequest
from sqlalchemy.ext.asyncio import AsyncSession

class ApprovalRouter:
    def __init__(self):
        # Initialize the handlers
        self.it_handler = ITHandler()
        self.finance_handler = FinanceHandler()
        self.clerk_admin_handler = ClerkAdminHandler()
        
        # wire: IT -> Finance -> ClerkAdmin
        self.it_handler.set_next(self.finance_handler)
        self.finance_handler.set_next(self.clerk_admin_handler)
        
        self._head = self.it_handler
        
    async def route(self, request: ApprovalRequest, db: AsyncSession) -> ApprovalRequest:
        return await self._head.handle(request, db)
