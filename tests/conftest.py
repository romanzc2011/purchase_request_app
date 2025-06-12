# # tests/conftest.py
# import os
# import sys
# import types

# # ─── 1) Make Pydantic Settings happy ────────────────────────────────────────────
# os.environ.update({
#     "LDAP_SERVER":           "ldap://localhost",
#     "LDAP_PORT":             "389",
#     "LDAP_USE_TLS":          "False",
#     "LDAP_SERVICE_USER":     "cn=svc,dc=ex,dc=org",
#     "LDAP_SERVICE_PASSWORD": "password",
#     "SEARCH_BASE":           "dc=ex,dc=org",
#     "IT_GROUP_DNS":          "cn=IT,dc=ex,dc=org",
#     "CUE_GROUP_DNS":         "cn=CUE,dc=ex,dc=org",
#     "ACCESS_GROUP_DNS":      "cn=Access,dc=ex,dc=org",
#     "VITE_API_URL":          "http://localhost:3000",
#     "JWT_SECRET_KEY":        "secret",
#     "APPROVALS_LINK":        "http://approve",
#     "SMTP_SERVER":           "smtp.example.org",
#     "SMTP_PORT":             "25",
#     "SMTP_EMAIL_ADDR":       "noreply@example.org",
# })

# # ─── 2) Stub out your dependencies module-level instances ───────────────────────
# import api.dependencies.pras_dependencies as deps

# # Dummy LDAPService that never binds
# class DummyLDAPService:
#     def __init__(self, *a, **k): pass
#     def _bind(self, *a, **k): return types.SimpleNamespace(bound=True)
#     def get_user_groups(self, *a, **k): return []
#     def get_user_info(self, *a, **k):   return {"username":"test","email":"test@x"}

# # Dummy SMTP etc.
# class DummySMTPService: 
#     def __init__(self, *a, **k): pass
#     def send_approver_email(self, *a,**k): pass
#     def send_requester_email(self, *a,**k): pass

# class DummyPDFService:
#     def __init__(self, *a, **k): pass
#     def create_pdf(self, *a,**k): return b"%PDF-1.4\n"

# class DummyUUIDService:
#     def __init__(self, *a, **k): pass
#     def new_uuid(self): return "00000000-0000-0000-0000-000000000000"

# class DummySearchService:
#     def __init__(self, *a, **k): pass
#     def create_whoosh_index(self): pass
#     def search(self, *a, **k): return []
#     def add_to_index(self, *a, **k): pass
#     def remove_from_index(self, *a, **k): pass

# class DummyAuthService:
#     def __init__(self, *a, **k): pass
#     def get_current_user(self, *a, **k): return {"username":"test","email":"test@x"}

# # Now override each singleton
# deps.ldap_service    = DummyLDAPService()
# deps.smtp_service    = DummySMTPService()
# deps.pdf_service     = DummyPDFService()
# deps.uuid_service    = DummyUUIDService()
# deps.search_service  = DummySearchService()
# deps.auth_service    = DummyAuthService()
# deps.renderer        = types.SimpleNamespace()   # since renderer was created module-level

# # ─── 3) Now it's safe to import your FastAPI app ───────────────────────────────
# from fastapi.testclient import TestClient
# from api.pras_api import app

# # ─── 4) Override your DB and Auth dependencies as before … ────────────────────
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from api.services.db_service import Base, get_session
# import pytest

import sys
import warnings
from pathlib import Path
import os
from dotenv import load_dotenv
import types

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
import api.services.ldap_service as ldap_mod
from api.schemas.purchase_schemas import PurchaseRequestLineItem, ItemStatus, FileAttachment

@pytest.fixture
def client(monkeypatch):
    """
    - Stubs out "get_current_user" and "get_email_address" so we don't hit real LDAP.
    """
    # Stub LDAPService before importing anything that triggers it
    # Replace the __init__ with a no-op that accepts the four expected parameters:
    ldap_mod.LDAPService.__init__ = lambda self, ldap_url=None, bind_dn=None, bind_password=None, group_dns=None: None
    
    # Now it's safe to import app (and everything that it imports under the hood).
    from fastapi.testclient import TestClient
    from api.pras_api import app
    
    # 1. Fake "get_current_user" so that dependency injection in FastAPI returns a known user
    async def fake_current_user():
        return LDAPUser(username="roman", email="roman@example.com", approved=["users"])
    app.dependency_overrides[auth_service.get_current_user] = fake_current_user
    
    # 2. Fake "get_email_address" so nobody goes to LDAP
    async def fake_get_email_address(username: str):
        return f"{username}@lawb.uscourts.gov"
    monkeypatch.setattr("api.dependencies.pras_dependencies.ldap_service.get_email_address", fake_get_email_address)
    
    # 3. Stub out anything that hits the real database or mutates state
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
    
    test_client = TestClient(app)
    return test_client