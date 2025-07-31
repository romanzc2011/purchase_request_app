from api.schemas.ldap_schema import LDAPUser
from api.utils.misc_utils import format_username
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
from api.schemas.enums import AssignedGroup, LDAPGroup
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import api.services.db_service as dbas

class ApproverPolicy:
    def __init__(self, user: LDAPUser):
        self.user = user
        
    async def deputy_chief_clerk_policy(
        self, 
        total_price: float, 
        current_status: str, 
        request: ApprovalRequest,
        db: AsyncSession
    ) -> bool:
        TESTING: bool = False
        logger.warning("#############################################################")
        logger.warning("TESTING MODE OFF")
        logger.warning("#############################################################")
        """
        - Clerk Admin (edwardtakara) can always approve.
        - Deputy Clerk (edmundbrown) can only approve if deputy_can_approve = True in DB.
        """
        username = format_username(self.user.username)
        
        # Only CUE group members can approve
        if not self.user.has_group(LDAPGroup.CUE_GROUP.value):
            logger.debug("User is not in CUE group, skipping")
            return False

        # Clerk Admin can always approve
        logger.debug("DEPUTY AND CLERK TESTING AREA")
        
        #*-----------------------------------------------------------------------------------------
        #* NON-TESTING CODE
        #*-----------------------------------------------------------------------------------------
        if not TESTING:
            # Grab the clerk admin from DB, clerk admin will always be able to approve
            #?-----------------------------------------------------------------------------------------
            #? CHIEF CLERK ADMIN
            #?-----------------------------------------------------------------------------------------
            #? This is for the chief clerk, which is edwardtakara
            stmt = select(dbas.WorkflowUser.active).where(
                dbas.WorkflowUser.department == AssignedGroup.CHIEF_CLERK.value,
                dbas.WorkflowUser.username == "edwardtakara"  # Simulating TED being the current user
            )
            logger.debug(f"Checking if chief clerk {username} is active")
            
            result = await db.execute(stmt)
            row = result.first()
            CHIEF_CLERK_ACTIVE = row and row.active
            logger.debug(f"CHIEF_CLERK_ACTIVE: {CHIEF_CLERK_ACTIVE}")
            CHIEF_CLERK_GROUP = self.user.has_group(LDAPGroup.CUE_GROUP.value)
            logger.debug(f"CHIEF_CLERK_GROUP: {CHIEF_CLERK_GROUP}")
            logger.debug(f"CHIEF_CLERK_ACTIVE: {CHIEF_CLERK_ACTIVE}")
            
            if (CHIEF_CLERK_ACTIVE and CHIEF_CLERK_GROUP):
                logger.debug("CHIEF_CLERK_ACTIVE and CHIEF_CLERK_GROUP are True, allowing approval")
                logger.debug("############################################################")
                logger.info("this line in prod to check if the current_user is edwardtakara because he can approve anything at anytime")
                logger.debug("CLERK ADMIN CAN APPROVE")
                logger.debug("############################################################")
                return True
            
            #?-----------------------------------------------------------------------------------------
            #? DEPUTY CLERK
            #?-----------------------------------------------------------------------------------------
            #? This is for the deputy clerk, which is edmundbrown
            stmt = select(dbas.WorkflowUser.active).where(
                dbas.WorkflowUser.department == AssignedGroup.DEPUTY_CLERK.value,
                dbas.WorkflowUser.username == username
            )
            logger.debug(f"Checking if deputy clerk {username} is active and proper permissions/group")
            logger.debug(f"User has group: {self.user.has_group(LDAPGroup.CUE_GROUP)}")
            #?-----------------------------------------------------------------------------------------
            result = await db.execute(stmt)
            row = result.first()
            deputy_clerk_active = row and row.active
            DEPUTY_CLERK_ACTIVE = (username == "edmundbrown" and deputy_clerk_active)
            logger.debug(f"DEPUTY_CLERK_ACTIVE: {DEPUTY_CLERK_ACTIVE}")

            if DEPUTY_CLERK_ACTIVE:
                logger.debug("############################################################")
                logger.info("this line in prod to check if the current_user is edwardtakara because he can approve anything at anytime")
                logger.debug("DEPUTY CLERK IS ACTIVE")
                logger.debug("############################################################")
                return True

            #!---------------------------------------------------------------------------------------
            #! BOTH ARE INACTIVE DEPUTY AND CHIEF CLERK
            #!-----------------------------------------------------------------------------------------
            if not (CHIEF_CLERK_ACTIVE and DEPUTY_CLERK_ACTIVE):
                """
                Semi-testing, trying logic for when TESTING is False, need to substitute romancampbell
                for edwardtakara or edmundbrown
                """
                logger.debug("PROGRAM IS IN SEMI - TESTING - Substitute romancampbell for edwardtakara")
                #!-----------------------------------------------------------------------------------------
                #! TESTING CODE
                stmt = select(
                    dbas.WorkflowUser.active,
                    dbas.WorkflowUser.email).where(
                        dbas.WorkflowUser.username == "roman_campbell"
                    )
                result = await db.execute(stmt)
                row = result.first()
                roman_test_user_active = row and row.active
                ROMAN_TEST_USER_ACTIVE = (username == "romancampbell" and roman_test_user_active)
                logger.debug(f"User has group: {self.user.has_group(LDAPGroup.CUE_GROUP.value)}")
                
                if ROMAN_TEST_USER_ACTIVE:
                    logger.debug("ROMAN_TEST_USER_ACTIVE is True, allowing approval")
                    return True
                #!-----------------------------------------------------------------------------------------

            # Deputy Clerk logic
            """
            This is pulling data from FinalApproval, which is a decision table and determining if request total price
            is under $250, if it is then edmundbrown (deputy clerk or here just deputy)
            """
            #? If testing this would be ROMAN_TEST_USER_ACTIVE
            if DEPUTY_CLERK_ACTIVE:
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
        elif TESTING:
            logger.debug("PROGRAM IS IN TESTING - Substitute romancampbell for edwardtakara")
            #!-----------------------------------------------------------------------------------------
            #! TESTING CODE
            ROMAN_TEST_USER_ACTIVE = await self.is_test_user_active(db)
            if ROMAN_TEST_USER_ACTIVE:
                logger.debug("ROMAN_TEST_USER_ACTIVE is True, allowing approval")
                return True
            #!-----------------------------------------------------------------------------------------
            #*-----------------------------------------------------------------------------------------
            #* END NON-TESTING CODE
            #*-----------------------------------------------------------------------------------------
    
    # ----------------------------------------------------------------------------------    
    # FINANCE HANDLER APPROVAL LOGIC
    # ----------------------------------------------------------------------------------
    def can_management_approve(self, fund: str, current_status: ItemStatus) -> bool:
        if current_status != ItemStatus.NEW_REQUEST:
            logger.debug(f"Request status is not NEW_REQUEST ({current_status}), skipping")
            return False
        return self.user.has_group("ACCESS_GROUP") and fund.startswith("092")

    # ----------------------------------------------------------------------------------
    # IT HANDLER APPROVAL LOGIC
    # ----------------------------------------------------------------------------------
    def can_it_approve(self, fund: str, current_status: ItemStatus) -> bool:
        if current_status != ItemStatus.NEW_REQUEST:
            logger.warning(f"Request status is not NEW_REQUEST ({current_status}), skipping")
            return False
        return self.user.has_group("IT_GROUP") and fund.startswith("511")
    
    # ----------------------------------------------------------------------------------
    # TEST USER ACTIVE CHECK
    # ----------------------------------------------------------------------------------
    async def is_test_user_active(self, db: AsyncSession) -> bool:
        """
        Check if the test user is active in the database.
        """
        username = format_username(self.user.username)
        stmt = select(dbas.WorkflowUser.active).where(
            dbas.WorkflowUser.username == "roman_campbell"  # Replace with the test user username if needed
        )
        result = await db.execute(stmt)
        row = result.first()
        return row and row.active if row else False