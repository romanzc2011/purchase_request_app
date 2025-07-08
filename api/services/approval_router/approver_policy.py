from api.schemas.ldap_schema import LDAPUser
from api.utils.misc_utils import format_username
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import api.services.db_service as dbas

class ApproverPolicy:
    def __init__(self, user: LDAPUser):
        self.user = user
        
    async def can_clerk_admin_approve(
        self, 
        total_price: float, 
        current_status: str, 
        request: ApprovalRequest,
        db: AsyncSession
    ) -> bool:
        """
        - Clerk Admin (edwardtakara) can always approve.
        - Deputy Clerk (edmundbrown) can only approve if deputy_can_approve = True in DB.
        """
        if current_status != ItemStatus.PENDING_APPROVAL:
            logger.debug(f"Request {request.uuid} is not in PENDING_APPROVAL status ({current_status}), skipping")
            return False
        
        ## FOR TESTING TO SEE PROGRESS
        if current_status == ItemStatus.PENDING_APPROVAL:
            logger.debug(f"Request {request.uuid} is in PENDING_APPROVAL status")

        if not self.user.has_group("CUE_GROUP"):
            logger.debug("User is not in CUE group, skipping")
            return False

        username = format_username(self.user.username)

        # Clerk Admin can always approve
        logger.debug("DEPUTY AND CLERK TESTING AREA")
        if username == "edwardtakara":
            logger.debug("CLERK ADMIN CAN APPROVE")
            return True
        # if username == "edwardtakara" or username == "romancampbell":  # TESTING
        #     logger.debug("CLERK ADMIN CAN APPROVE")
        #     return True

        # Deputy Clerk logic
        if username == "edmundbrown" or username == "romancampbell":  # TESTING
            stmt = select(dbas.FinalApproval.deputy_can_approve).where(
                dbas.FinalApproval.line_item_uuid == request.uuid
            )
            result = await db.execute(stmt)
            row = result.first()
            deputy_can_approve = row and row.deputy_can_approve

            if deputy_can_approve:
                logger.debug("Deputy Clerk can approve request under $250")
                return True
            else:
                logger.debug("Deputy Clerk not allowed to approve this request")
                return False

        logger.debug("Only Deputy Clerk and Clerk Admin can approve requests")
        return False

    def can_finance_approve(self, fund: str, current_status: ItemStatus) -> bool:
        if current_status != ItemStatus.NEW_REQUEST:
            logger.debug(f"Request status is not NEW_REQUEST ({current_status}), skipping")
            return False
        return self.user.has_group("ACCESS_GROUP") and fund.startswith("092")

    def can_it_approve(self, fund: str, current_status: ItemStatus) -> bool:
        if current_status != ItemStatus.NEW_REQUEST:
            logger.info(f"Request status is not NEW_REQUEST ({current_status}), skipping")
            return False
        return self.user.has_group("IT_GROUP") and fund.startswith("511")