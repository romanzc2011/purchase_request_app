from api.services.approval_router.approval_handlers import ITHandler, FinanceHandler, ClerkAdminHandler, Handler
from api.schemas.approval_schemas import ApprovalRequest
from sqlalchemy.ext.asyncio import AsyncSession
from api.schemas.ldap_schema import LDAPUser
from api.dependencies.pras_dependencies import auth_service
from api.services.ldap_service import LDAPService

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
    
    def start_handler(self, handler: Handler):
        """
        Allow manual override of the starting handler
        """
        self._head = handler
        return self
        
    async def route(
        self, 
        request: ApprovalRequest, 
        db: AsyncSession,
        current_user: LDAPUser,
        ldap_service: LDAPService
    ) -> ApprovalRequest:
        return await self._head.handle(request, db, current_user, ldap_service)
