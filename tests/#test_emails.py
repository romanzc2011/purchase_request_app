from api.schemas.email_schemas import EmailPayloadRequest
import json
import pytest

def make_dummy_payload():
    return {
        "requester": "roman",
        "ID": "REQ-2025-0001",
        "add_comments": [
            "Training not available",
            "Does not meet employee needs"
        ],
        "items": [
            {
                "UUID": "test-uuid-1",
                "ID": "REQ-2025-0001",
                "requester": "roman",
                "phoneext": "1234",
                "datereq": "2025-06-05",
                "order_type": "QUARTERLY_ORDER",
                "item_description": "Wireless Keyboard and Mouse Combo",
                "justification": "Replacement for broken peripherals in the main office",
                "quantity": 5,
                "price": 45.00,
                "price_each": 45.00,
                "total_price": 225.00,
                "fund": "OF-SUP-01",
                "location": "LKCH/C",
                "budget_obj_code": "6100",
                "status": "NEW REQUEST"
            }
        ],
        "itemCount": 1
    }

@pytest.mark.usefixtures("client")
def test_email_rendering(client):
    payload = make_dummy_payload()
    # Convert payload to JSON string for form data
    payload_json = json.dumps(payload)
    response = client.post(
        "/api/sendToPurchaseReq",
        data={"payload_json": payload_json},
        files=[]  # Empty files list since we're not testing file uploads
    )
    
    if response.status_code != 200:
        print("\nValidation Error Details:")
        print(response.json())
    
    assert response.status_code == 200
    
    sent = client.captured_msgs
    assert len(sent) == 2
    assert response.json() == {"message": "All work completed"}
    
    for direction, email_payload in sent:
        print(f"\n---- {direction.upper()} EMAIL ----")
        print("Subject:", email_payload.subject)
        print("\n[---- EMAIL PAYLOAD ----]")
        print(json.dumps(email_payload.model_dump(), indent=2, default=str))
        
        if hasattr(email_payload, "html_body"):
            print("\n[---- HTML BODY ----]")
            print(email_payload.html_body)  
        if hasattr(email_payload, "text_body"):
            print("\n[---- TEXT BODY ----]")
            print(email_payload.text_body)
