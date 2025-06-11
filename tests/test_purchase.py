def test_create_new_id_increments(client):
    resp1 = client.post("/api/create_new_id")
    assert resp1.status_code == 200
    id1 = resp1.json()["id"]
    assert id1 == "LAWB0001"
    
def test_send_purchase_request(client):
    # build a minimal payload matching PurchaseRequestPayload schema
    payload = {
      "requester": "testuser",
      "items": [
        {
          "id": "LAWB0001",
          "uuid": "11111111-1111-1111-1111-111111111111",
          "irq1_id": None,
          "requester": "testuser",
          "phoneext": "1234",
          "datereq": "2025-06-11",
          "dateneed": None,
          "order_type": "STANDARD",
          "item_description": "foo",
          "justification": "bar",
          "train_not_aval": False,
          "needs_not_meet": False,
          "quantity": 1,
          "price_each": 10.0,
          "total_price": 10.0,
          "fund": "51140E",
          "location": "LKCH/C",
          "budget_obj_code": "3113",
          "status": "NEW REQUEST",
          "file_attachments": []
        }
      ],
      "itemCount": 1
    }
    
    # Call endpoint
    resp = client.post(
        "/api/send_to_purchase_req",
        json=payload,
        headers={"Authorization": f"Bearer faketoken"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Purchase request sent to approval"
    