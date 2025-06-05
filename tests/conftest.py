import sys
import warnings
from pathlib import Path
import os
from dotenv import load_dotenv

# Get the project root directory
project_root = str(Path(__file__).parent.parent)

# Add the project root directory to the Python path
sys.path.insert(0, project_root)

# Load environment variables from .env file BEFORE importing any settings
load_dotenv(project_root + "/.env")

# Filter out pyasn1 deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pyasn1")

# Now import the rest of the modules
from datetime import datetime
import json
from io import BytesIO
from typing import List
from api.schemas.email_schemas import EmailPayloadRequest
import pytest
from fastapi.testclient import TestClient
from api.pras_api import app
from api.dependencies.pras_dependencies import *
from api.schemas.auth_schemas import LDAPUser
from api.schemas.purchase_schemas import PurchaseItem, ItemStatus, FileAttachment

ldap_service = LDAPService(
    ldap_url=settings.LDAP_SERVER,
    bind_dn=settings.LDAP_SERVICE_USER,
    bind_password=settings.LDAP_SERVICE_PASSWORD,
    group_dns=settings.IT_GROUP_DNS
)

@pytest.fixture
def client(monkeypatch):
    """
    Build a TestClient that:
     - Stubs out "get_current_user" and "get_email_address" so we don't hit real LDAP.
     - Stubs out "get_next_request_id", "process_purchase_data", "purchase_req_commit"
       so we don't touch the real database.
     - Stubs out file-saving and PDF-generation to return fake paths.
     - Replaces send_approver_email/send_requester_email with a fake that *captures* the payload.
     - Leaves template-rendering code intact.
    """
    # 0. Patch LDAPService.__init__ before importing anything that triggers it.
    #    This ensures that any code doing `LDAPService()` at module scope will not error.
    import api.services.ldap_service as ldap_mod
    # Replace the __init__ with a no-op that accepts the four expected parameters:
    ldap_mod.LDAPService.__init__ = lambda self, ldap_url=None, bind_dn=None, bind_password=None, group_dns=None: None

    # Now it's safe to import app (and everything that it imports under the hood).
    from fastapi.testclient import TestClient
    from api.pras_api import app

    # 1. Fake "get_current_user" so that dependency injection in FastAPI returns a known user
    async def fake_get_current_user(token: str = None) -> LDAPUser:
        return LDAPUser(username="roman", email="roman@example.com", groups=["users"])
    app.dependency_overrides[auth_service.get_current_user] = fake_get_current_user

    # 2. Fake "get_email_address" so nobody goes to LDAP
    async def fake_get_email_address(username: str):
        return f"{username}@lawb.uscourts.gov"
    monkeypatch.setattr("api.dependencies.pras_dependencies.ldap_service.get_email_address", fake_get_email_address)

    # 3. Stub out anything that hits the real database or mutates state
    monkeypatch.setattr("api.pras_api.dbas.get_next_request_id", lambda: "REQ001")
    monkeypatch.setattr("api.pras_api.process_purchase_data", lambda payload: payload)
    monkeypatch.setattr("api.pras_api.purchase_req_commit", lambda data, user: None)


    # 4. Stub out file saving (we don't want to write to disk in tests)
    async def fake_save_files(shared_id, file):
        # Return a predictable "fake" path for each uploaded file
        return f"/fakepath/{shared_id}_{file.filename}"
    monkeypatch.setattr("api.pras_api._save_files", fake_save_files)

    # 5. Stub out PDF generation (so you don't need wkhtmltopdf or real rendering)
    async def fake_generate_pdf(payload, shared_id, uploaded_files):
        return f"/fakepdfs/{shared_id}.pdf"
    monkeypatch.setattr("api.pras_api.generate_pdf", fake_generate_pdf)

    ##############################################################################################
    # EMAIL TESTING
    ##############################################################################################
    # 5) Use real email sending instead of mocks
    from api.services.smtp_service import send_approver_email, send_requester_email
    
    # Keep the capture functionality but also send real emails
    captured_msgs = []
    async def real_send_approver_email(email_payload: EmailPayloadRequest):
        captured_msgs.append(("approver", email_payload))
        await send_approver_email(email_payload)
    async def real_send_requester_email(email_payload: EmailPayloadRequest):
        captured_msgs.append(("requester", email_payload))
        await send_requester_email(email_payload)

    monkeypatch.setattr(
        "api.pras_api.smtp_service.send_approver_email",
        real_send_approver_email,
    )
    monkeypatch.setattr(
        "api.pras_api.smtp_service.send_requester_email",
        real_send_requester_email,
    )
    
    test_client = TestClient(app)
    test_client.captured_msgs = captured_msgs
    return test_client