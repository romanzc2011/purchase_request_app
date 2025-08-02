import asyncio
from typing import List
from api.dependencies.pras_dependencies import auth_service, ldap_service
from api.services.approval_router.approval_router import ApprovalRouter
from api.schemas.approval_schemas import ApprovalRequest, RequestPayload
from api.schemas.enums import ItemStatus
from api.services.db_service import AsyncSessionLocal, PurchaseRequestHeader, Approval, PendingApproval
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

async def create_test_data(db: AsyncSession):
    """Create test data in the database"""
    # Create a test purchase request header
    purchase_request = PurchaseRequestHeader(
        ID="REQ-2025-001",
        requester="edmundbrown",
        phoneext=9999,
        datereq="2025-01-01",
        dateneed="2025-01-10",
        orderType="SUPPLY"
    )
    db.add(purchase_request)
    await db.flush()
    
    # Create a test approval
    approval = Approval(
        purchase_request_id="REQ-2025-001",
        requester="edmundbrown",
        phoneext=9999,
        datereq="2025-01-01",
        itemDescription="Test chair",
        justification="Testing approval workflow",
        budgetObjCode="6001",
        fund="092000",
        priceEach=600.00,
        totalPrice=600.00,
        location="Office 1",
        quantity=1,
        status=ItemStatus.NEW_REQUEST
    )
    db.add(approval)
    await db.flush()
    
    # Create a test pending approval
    pending_approval = PendingApproval(
        purchase_request_id="REQ-2025-001",
        line_item_uuid="abc-uuid",
        approvals_uuid=approval.UUID,
        assigned_group="MANAGEMENT",
        status=ItemStatus.NEW_REQUEST
    )
    db.add(pending_approval)
    await db.commit()
    
    return approval.UUID, pending_approval.pending_approval_id

async def main():
    # STEP 1: Set the override
    auth_service.set_test_user_override(
        username="edmundbrown",
        email="romancampbell@lawb.uscourts.gov",
        groups=["CUE_GROUP"]
    )

    # STEP 2: Create database session and test data
    async with AsyncSessionLocal() as db:
        # Create test data
        approval_uuid, pending_approval_id = await create_test_data(db)
        
        # STEP 3: Build fake request with correct schema fields
        fake_request = ApprovalRequest(
            id="REQ-2025-001",
            uuid="abc-uuid",
            pending_approval_id=pending_approval_id,  # Use the real pending approval ID
            fund="092000",  # Routes to Management
            status=ItemStatus.NEW_REQUEST,
            total_price=600.00,
            action="APPROVE",
            approver="edmundbrown"
        )
        
        # STEP 4: Get current user and route
        router = ApprovalRouter()
        current_user = await auth_service.get_current_user()
        
        try:
            result = await router.route(fake_request, db, current_user, ldap_service)
            print("✅ Route completed:", result)
        except Exception as e:
            print(f"❌ Error during routing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
