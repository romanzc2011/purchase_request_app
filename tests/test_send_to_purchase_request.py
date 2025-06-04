from datetime import datetime
import json
from io import BytesIO
import pytest
from fastapi.testclient import TestClient

from api.pras_api import app
from api.schemas.auth_schemas import LDAPUser
from api.schemas.purchase_schemas import PurchaseItem, ItemStatus, FileAttachment

@pytest.fixture
def client(monkeypatch):
    # —— PATCH STUBS —— (copy/paste exactly)
    async def fake_get_current_user():
        return LDAPUser(username="roman", email="roman@example.com", groups=["users"])
    monkeypatch.setattr("api.pras_api.auth_service.get_current_user", fake_get_current_user)

    async def fake_get_email_address(username: str):
        return f"{username}@lawb.uscourts.gov"
    monkeypatch.setattr("api.pras_api.ldap_service.get_email_address", fake_get_email_address)

    monkeypatch.setattr("api.pras_api.dbas.get_next_request_id", lambda: "REQ001")
    monkeypatch.setattr("api.pras_api.process_purchase_data", lambda item: item)
    monkeypatch.setattr("api.pras_api.purchase_req_commit", lambda data, user: None)

    async def fake_save_files(shared_id, file):
        return f"/fakepath/{shared_id}_{file.filename}"
    monkeypatch.setattr("api.pras_api._save_files", fake_save_files)

    async def fake_generate_pdf(payload, shared_id, uploaded_files):
        return f"/fakepdfs/{shared_id}.pdf"
    monkeypatch.setattr("api.pras_api.generate_pdf", fake_generate_pdf)

    async def fake_send_approver_email(payload): pass
    async def fake_send_requester_email(payload): pass
    monkeypatch.setattr("api.pras_api.smtp_service.send_approver_email", fake_send_approver_email)
    monkeypatch.setattr("api.pras_api.smtp_service.send_requester_email", fake_send_requester_email)

    return TestClient(app)


def make_dummy_payload():
    """
    Returns a dict matching your PurchaseRequestPayload (with one PurchaseItem inside).
    All required fields are included so Pydantic validation passes.
    """
    now_iso = datetime.utcnow().isoformat()  # e.g. "2025-06-04T12:34:56.789Z"
    return {
        "requester": "roman",
        "items": [
            {
                # PurchaseItem fields:
                "UUID":          "00000000-0000-0000-0000-000000000000",
                "ID":            "TEMP-1",
                "requester":     "roman",
                "phoneext":      "1234",                       # must be a string in your model
                "datereq":       "2025-06-04",                  # Pydantic will coerce to date
                "orderType":     "standard",                    # e.g. "standard" or whatever your app expects
                "itemDescription": "Test item description",
                "justification": "Because we need to test",
                "trainNotAval":   False,
                "needsNotMeet":   False,
                "quantity":       1,
                "priceEach":      15.0,
                "price":          15.0,                         # if your model has both price and priceEach
                "totalPrice":     15.0,                         # quantity * priceEach
                "fund":           "ABC123",
                "location":       "Room 101",
                "budgetObjCode":  "XYZ789",
                "status":         "NEW REQUEST",                # the string value of ItemStatus.NEW_REQUEST
                "dateneed":       "2025-06-10",                  # optional, but include it if your model requires it
                "fileAttachments": None,                        # or omit if your Pydantic schema has a default
                "createdTime":    now_iso                        # optional, but include if not defaulted
            }
        ]
    }

def post_dummy(client, endpoint: str, payload_dict: dict, filename="dummy.pdf", file_bytes=b"dummy"):
    """
    Posts multipart/form-data with a JSON payload under "payload_json" and a single file under "files".
    """
    json_str = json.dumps(payload_dict)
    fake_file = BytesIO(file_bytes)
    fake_file.name = filename

    return client.post(
        endpoint,
        data={"payload_json": json_str},
        files={"files": (filename, fake_file, "application/pdf")}
    )
