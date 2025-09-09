from api.services.approval_router.approval_handlers import ITHandler, ClerkAdminHandler, Handler, ManagementHandler
from api.schemas.approval_schemas import ApprovalRequest
from sqlalchemy.ext.asyncio import AsyncSession
from api.schemas.ldap_schema import LDAPUser
from api.dependencies.pras_dependencies import auth_service
from api.services.ldap_service import LDAPService
import api.services.socketio_server.sio_events as sio_events
from loguru import logger

class ApprovalRouter:
    def __init__(self):
        logger.info("ApprovalRouter initialized")
        
        # Initialize the handlers
        self.it_handler = ITHandler()  # Matt
        self.management_handler = ManagementHandler()  # Lela, Edmund
        self.clerk_admin_handler = ClerkAdminHandler() # Edmund, Ted
        
        # wire: IT -> Finance -> ClerkAdmin
        self.it_handler.set_next(self.management_handler)
        self.management_handler.set_next(self.clerk_admin_handler)
        
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
        # Update ALL handlers in the chain with current_user if they don't have it
        self._update_handlers_with_user(current_user)
        
        return await self._head.handle(request, db, current_user, ldap_service)
    
    def _update_handlers_with_user(self, current_user: LDAPUser):
        """Update all handlers in the chain with current_user"""
        handler = self._head
        while handler:
            if not hasattr(handler, 'current_user') or handler.current_user is None:
                handler.current_user = current_user
                handler.sid = sio_events.get_user_sid(current_user)
            handler = handler._next
