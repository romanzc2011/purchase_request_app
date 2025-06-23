from api.schemas.ldap_schema import LDAPUser
from api.utils.misc_utils import format_username
from api.schemas.misc_schemas import ItemStatus
from api.schemas.approval_schemas import ApprovalRequest
from loguru import logger

class ApproverPolicy:
    def __init__(self, user: LDAPUser):
        self.user = user
    
    #######################################################
    # DEFINE APPROVER GROUPS
    #######################################################
    def is_clerk_admin(self) -> bool:
        return self.user.has_group("CUE")
    
    def is_finance_approver(self) -> bool:
        return self.user.has_group("ACCESS_GROUP")
    
    def is_it_approver(self) -> bool:
        return self.user.has_group("IT_GROUP")
    
    #######################################################
    # DEFINE APPROVER POLICIES
    #######################################################
    def deputy_clerk(self, total_price: float) -> bool: # PROD ONLY
        username = format_username(self.user.username)
        if self.is_clerk_admin() and total_price < 250 and username == "edmundbrown":
            return True
        else:
            return False
        
    def clerk_admin(self) -> bool: # PROD ONLY
        username = format_username(self.user.username)
        if self.is_clerk_admin() and username == "edwardtakara":
            return True
        else:
            return False
        
    # Flow to determine if to proceed with approval
    def is_clerk_admin(self) -> bool:
        return self.user.has_group("CUE")

    def is_deputy_clerk(self) -> bool:
        return self.is_clerk_admin() and format_username(self.user.username) == "edmundbrown"

    def is_clerk_admin_final(self) -> bool:
        return self.is_clerk_admin() and format_username(self.user.username) == "edwardtakara"

    def can_proceed_with_approval(self, total_price: float, current_status: str, request: ApprovalRequest) -> bool:
        if current_status != ItemStatus.PENDING_APPROVAL:
            logger.info(f"ClerkAdmin Handler: Request {request.uuid} is not in PENDING_APPROVAL status ({current_status}), skipping")
            return False

        if total_price < 250:
            if self.is_deputy_clerk():
                logger.info("CUE Policy: Deputy Clerk (Edmund) can approve (price < $250)")
                return True
            else:
                logger.info("CUE Policy: Only Deputy Clerk can approve requests under $250")
                return False
        else:
            if self.is_clerk_admin_final():
                logger.info("CUE Policy: Clerk Admin (Edward) can approve (price >= $250)")
                return True
            else:
                logger.info("CUE Policy: Only Clerk Admin can approve requests over $250")
                return False
        
    def finance_approver(self, fund: str) -> bool:
        if self.is_finance_approver() and fund.startswith("092"):
            return True
        
    def it_approver(self, fund: str) -> bool:
        if self.is_it_approver() and fund.startswith("511"):
            return True
        else:
            return False
        
	# TESTING POLICY
    def TEST_MASTER_POLICY(self) -> bool:
        if self.clerk_admin() and self.finance_approver("092") and self.it_approver("511"):
            return True
        else:
            return False
        