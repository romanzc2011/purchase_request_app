from api.schemas.ldap_schema import LDAPUser
from api.utils.misc_utils import format_username
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
from api.schemas.enums import AssignedGroup, CueClerk, LDAPGroup
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import api.services.db_service as dbas

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
        
        if await self._is_test_user_active(db):
            logger.debug(f"Test user is active, approving request")
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
            dbas.WorkflowUser.username == "roman_campbell"
        )
        result = await db.execute(stmt)
        row = result.first()
        return self.username == "romancampbell" and bool(row and row.active)
    
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
    # DEPUTY/CHIEF CLERK APPROVAL LOGIC
    # ----------------------------------------------------------------------------------
    async def deputy_chief_clerk_policy(
        self,
        total_price: float,
        current_status: ItemStatus,
        request: ApprovalRequest,
        db: AsyncSession
    ) -> bool:
        """
        Determine if deputy or chief clerk can approve the request
        """
        # Check if user has clerk admin permissions
        if not self.user.has_group(LDAPGroup.CUE_GROUP.value):
            logger.debug("User does not have CUE_GROUP permissions")
            return False
        
        # Check if the request is in a state that can be approved
        if current_status not in [ItemStatus.NEW_REQUEST, ItemStatus.PENDING_APPROVAL]:
            logger.debug(f"Request status {current_status} cannot be approved by clerk admin")
            return False
        
        # Check if deputy can approve based on price
        if dbas.can_deputy_approve(total_price) and self.username == CueClerk.DEPUTY_CLERK.value:
            logger.success("Deputy can approve based on price")
            return True
        
        # Check if chief clerk is active and is the current user
        if await self._is_chief_clerk_active(db) and self.username == CueClerk.CHIEF_CLERK.value:
            logger.success("Chief clerk is active and can approve")
            return True
        
        # Check if test user is active
        if await self._is_test_user_active(db):
            logger.success("Test user is active and can approve")
            return True
        
        logger.debug("User cannot approve this request")
        return False