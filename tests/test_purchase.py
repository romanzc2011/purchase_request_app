from api.schemas.auth_schemas import LDAPUser
import json


def test_create_new_id_increments(client):
    resp1 = client.post("/api/create_new_id")
    assert resp1.status_code == 200
    id1 = resp1.json()["id"]
    assert id1 == "LAWB0006"
    
def test_send_purchase_request(client):
    # build a minimal payload matching PurchaseRequestPayload schema
    item = {
        "uuid": "11111111-2222-3333-4444-555555555555",
        "id": "LAWB0006",
        "requester": "testuser",
        "phoneext": "1234",
        "datereq": "2025-06-12",
        "order_type": "STANDARD",
        "item_description": "Sample item",
        "justification": "This is a justification for the purchase",
        "add_comments": ["First manual comment", "Second manual comment"],
        "train_not_aval": None,
        "needs_not_meet": None,
        "quantity": 1,
        "price_each": 100.0,
        "total_price": 100.0,
        "fund": "51140E",
        "location": "LKCH/C",
        "budget_obj_code": "3113",
        "status": "NEW REQUEST",
        "dateneed": "2025-06-20",
        "file_attachments":[
            {"attachment":"VGhpciBpcyBhIHRlc3QgYXR0YWNobWVudA==",
            "name":"test.pdf","type":"application/pdf","size":1024}
        ],
        "created_time": "2025-06-12T10:40:00Z"
    }
    
    wrapper = {
    "requester": "testuser",
    "items": [item],
    "item_count": 1
}

    # Call endpoint with form data
    resp = client.post(
        "/api/send_to_purchase_req",
        data={"payload_json": json.dumps(wrapper)},
        headers={"Authorization": f"Bearer faketoken"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Purchase request sent to approval"
    
async def fake_current_user():
    return LDAPUser(username="roman", email="roman@example.com", approved=["users"])
    