from api.schemas.ldap_schema import LDAPUser
from api.utils.misc_utils import format_username
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
from api.schemas.enums import AssignedGroup, CueClerk, LDAPGroup
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import api.services.db_service as dbas

def _norm(u: str) -> str:
    return (u or "").strip().lower()

class ApproverPolicy:
    def __init__(self, user: LDAPUser):
        self.user = user
        self.username = user.username
    
    # ----------------------------------------------------------------------------------
    # CLERK ADMIN APPROVAL LOGIC
    # ----------------------------------------------------------------------------------
    async def can_clerk_admin_approve(
        self, 
        request: ApprovalRequest,
        db: AsyncSession
    ):
        if not self.user.has_group(LDAPGroup.CUE_GROUP.value):
            return False
        
        if await self._is_chief_clerk_active(db):
            logger.debug(f"Chief Clerk is active, approving request")
            return True
        
        if await self._is_deputy_clerk_active(db):
            logger.debug(f"Deputy Clerk is active, approving request")
            return True
        
        if await self._check_deputy_can_approve(request, db):
            logger.debug(f"Deputy can approve, approving request")
            return True
        
        return False
    
    # ----------------------------------------------------------------------------------
    # CLERK ACTIVE CHECKS
    # ----------------------------------------------------------------------------------
    async def _is_chief_clerk_active(self, db: AsyncSession) -> bool:
        stmt = select(dbas.WorkflowUser.active).where(
            dbas.WorkflowUser.department == AssignedGroup.CHIEF_CLERK.value,
            dbas.WorkflowUser.username == CueClerk.CHIEF_CLERK.value
        )
        result = await db.execute(stmt)
        row = result.first()
        return bool(row and row.active)
    
    async def _is_deputy_clerk_active(self, db: AsyncSession) -> bool:
        stmt = select(dbas.WorkflowUser.active).where(
            dbas.WorkflowUser.department == AssignedGroup.DEPUTY_CLERK.value,
            dbas.WorkflowUser.username == CueClerk.DEPUTY_CLERK.value
        )
        result = await db.execute(stmt)
        row = result.first()
        return bool(row and row.active)
    
    async def _check_deputy_can_approve(self, request: ApprovalRequest, db: AsyncSession) -> bool:
        stmt = select(dbas.FinalApproval.deputy_can_approve).where(
            dbas.FinalApproval.line_item_uuid == request.line_item_uuid,
        )
        result = await db.execute(stmt)
        row = result.first()
        return bool(row and row.deputy_can_approve)
    
    async def _is_test_user_active(self, db: AsyncSession) -> bool:
        stmt = select(dbas.WorkflowUser.active).where(
            dbas.WorkflowUser.username == CueClerk.TEST_USER.value
        )
        result = await db.execute(stmt)
        row = result.first()
        return format_username(self.username) == CueClerk.TEST_USER.value and bool(row and row.active)
    
    # ----------------------------------------------------------------------------------    
    # MANAGEMENT HANDLER APPROVAL LOGIC (LELA, EDMUND)
    # ----------------------------------------------------------------------------------
    def can_management_approve(self, fund: str, current_status: ItemStatus) -> bool:
        if current_status != ItemStatus.NEW_REQUEST:
            logger.debug(f"Request status is not NEW_REQUEST ({current_status}), skipping")
            return False
        return self.user.has_group(LDAPGroup.CUE_GROUP.value) and fund.startswith("092")

    # ----------------------------------------------------------------------------------
    # IT HANDLER APPROVAL LOGIC
    # ----------------------------------------------------------------------------------
    def can_it_approve(self, fund: str, current_status: ItemStatus) -> bool:
        if current_status != ItemStatus.NEW_REQUEST:
            logger.warning(f"Request status is not NEW_REQUEST ({current_status}), skipping")
            return False
        return self.user.has_group(LDAPGroup.IT_GROUP.value) and fund.startswith("511")
    
    # ----------------------------------------------------------------------------------
    # CAN FULL APPROVE
    # ----------------------------------------------------------------------------------
    async def can_fully_approve(
        self,
        total_price: float,
        current_status: ItemStatus,
        db: AsyncSession
    ) -> bool:
        # Must have clerk admin perms
        logger.warning(f"DEBUG: {self.username}")
        logger.warning(f"DEBUG {format_username(self.username)}")
        
        if not self.user.has_group(LDAPGroup.CUE_GROUP.value):
            logger.warning("User is not a member of CUE")
            return False
        
        # Chief: must be active and be the chief account
        if (await self._is_chief_clerk_active(db) and format_username(self.username) == CueClerk.CHIEF_CLERK.value):
            logger.success("CHIEF CLERK is current user and can approve")
            return True
        
        # Deputy: must be active , be the deputy account, and whithin price limit
        if (await self._is_deputy_clerk_active(db)
            and format_username(self.username) == CueClerk.DEPUTY_CLERK.value
            and dbas.can_deputy_approve(total_price)):
            logger.success("DEPUTY CLERK is current user and can approve")
            return True
        
        # Test user override, must be active
        if (await self._is_test_user_active(db) and format_username(self.username) == CueClerk.TEST_USER.value):
            logger.success("TEST USER active")
            return True
        
        return False