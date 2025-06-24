import pytest
from unittest.mock import AsyncMock
from api.schemas.ldap_schema import LDAPUser
from api.schemas.approval_schemas import ApprovalRequest
from api.policies.approver_policy import ApproverPolicy
from api.schemas.misc_schemas import ItemStatus

@pytest.mark.asyncio
async def test_edmund_cannot_approve_over_250_when_flag_false():
    user = LDAPUser(username="ADU\\edmundbrown", groups=["CUE"])
    request = ApprovalRequest(
        uuid="abc-123",
        id="REQ001",
        total_price=300,
        fund="511000",
        requester="someone",
        requester_email="someone@example.com",
        approver="edmundbrown",
        items=[]
    )
    
    # Fake db with deputy_can_approve = False
    fake_db = AsyncMock()
    fake_db.execute.return_value.first.return_value = type("Row", (), {"deputy_can_approve": False})()

    policy = ApproverPolicy(user)
    result = await policy.can_clerk_admin_approve(300, ItemStatus.PENDING_APPROVAL, request, fake_db)

    assert result is False

@pytest.mark.asyncio
async def test_edward_can_approve_anything():
    user = LDAPUser(username="ADU\\edwardtakara", groups=["CUE"])
    request = ApprovalRequest(
        uuid="abc-123",
        id="REQ001",
        total_price=9999,
        fund="511000",
        requester="someone",
        requester_email="someone@example.com",
        approver="edwardtakara",
        items=[]
    )

    # Fake db result isn't even used here
    fake_db = AsyncMock()

    policy = ApproverPolicy(user)
    result = await policy.can_clerk_admin_approve(9999, ItemStatus.PENDING_APPROVAL, request, fake_db)

    assert result is True
