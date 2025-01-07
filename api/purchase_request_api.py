from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import json
import os
import purchase_request_database as db
import queue
import threading

"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PURCHASE REQUEST APP
Will be used to keep track of purchase requests digitally through a central UI. This is the backend that will service
the UI.
"""
lock = threading.Lock()
processed_data_shared = None
db_path = os.path.join(os.path.dirname(__file__), "db", "purchase_requests.db")
executor = ThreadPoolExecutor(max_workers=5)

app = Flask(__name__)
CORS(app)

# Dictionary for sql column
purchase_cols = {
    'req_id': None,
    'requester': None,
    'phoneext': None,
    'datereq': None,
    'dateneed': None,
    'orderType': None,
    'fileAttachments': None,
    'itemDescription': None,
    'justification': None,
    'addComments': None,
    'learnAndDev': { 'trainNotAval': False, 'needsNotMeet': False },
    'budgetObjCode': None,
    'fund': None,
    'price': None,
    'location': None,
    'quantity': None,
}

# Dictionary for approval data
approvals_cols = {
    'req_id': None,
    'budgetObjCode': None,
    'fund': None,
    'location': None,
    'quantity': None,
    'priceEach': None,
    'totalPrice': None,
    'status': None
}

##########################################################################
## API FUNCTIONS
##########################################################################

##########################################################################
## SEND TO APPROVALS -- being sent from the purchase req submit
@app.route('/sendToPurchaseReq', methods=['POST'])
def setPurchaseRequest():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Submit the task to thread executor
    future = executor.submit(purchase_bg_task, data, db_path, "sendToPurchaseReq")
    future = executor.submit(purchase_bg_task, data, db_path, "insertApprovalData")
    
    return jsonify({"message": "Processing started in background"})
    
##########################################################################
## GET APPROVAL DATA
@app.route('/getApprovalData', methods=['GET'])
def getApprovalData():
    try:
        db.createApprovalsTbl(db_path)
        table = "approvals"
        query = f"SELECT * FROM {table}"
        data = db.fetch_rows(db_path, query, table)
        print(f"{data}")
        
        getApprovalStatus(table)
        return jsonify(data), 200
    
    except Exception as e:
        print(f"Error fetching approval data: {e}")
        return jsonify({"error": "Failed to fetch data"}), 500
    
##########################################################################
## PROCESS PURCHASE DATA
def process_purchase_data(data):
    with lock:
        # Populate purchase_cols with appropriate data from api call
        for item in data['dataBuffer']:
            for k, v in item.items():
                if k in purchase_cols:
                    purchase_cols[k] = v
                    
        # Extract the learnAndDev element
        if 'learnAndDev' in purchase_cols:
            purchase_cols['trainNotAval'] = purchase_cols['learnAndDev']['trainNotAval']
            purchase_cols['needsNotMeet'] = purchase_cols['learnAndDev']['needsNotMeet']
            del purchase_cols['learnAndDev']
          
        # Calc and separate price of each and total
        if 'price' in purchase_cols and 'quantity' in purchase_cols:
            try:
                purchase_cols['priceEach'] = float(purchase_cols['price'])
                purchase_cols['quantity'] = int(purchase_cols['quantity'])
                
                # Validate ranges
                if purchase_cols['priceEach'] < 0 or purchase_cols['quantity'] <= 0:
                    raise ValueError("Price must be non-negative, and quantity must be greater than zero.")
                
                # Calculate totalPrice
                purchase_cols['totalPrice'] = round(purchase_cols['priceEach'] * purchase_cols['quantity'], 2)
                
            except ValueError as e:
                print("Invalid price or quantity:")
                purchase_cols['totalPrice'] = 0
            
            del purchase_cols['price']
        
        # Show this is a new request 0=FALSE 1=TRUE
        purchase_cols['new_request'] = 1
        purchase_cols['approved'] = 0
        
    return purchase_cols

##########################################################################
## PROCESS APPROVAL DATA --- send new request  to approvals
def processApprovalsData():
    approved = None
    # Is this a new request or has it been approved already
    if purchase_cols['new_request'] == 1:
        approvals_cols['status'] == "NEW REQUEST"
        # Not new? Was it approved or denied?
    elif purchase_cols['new_request'] == 0:
        
        approved = getApprovalStatus("approvals", purchase_cols['req_id'])
        if approved == 1:
            approvals_cols['status'] = "APPROVED"
        if approved == 0:
            approvals_cols['status'] = "DENIED"
    
    # Populate approval data 
    with lock:
        for item in purchase_cols:
            for k, v in item.items():
                if k in approvals_cols:
                    approvals_cols[k] = v

##########################################################################
## GET STATUS OF APPROVALS
def getApprovalStatus(table, req_id):
    query = """SELECT approved FROM {table}
               WHERE req_id = {req_id}
            """
    
    approved_data = db.fetch_rows(db_path, query, table)
    return approved_data
    
##########################################################################
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
def purchase_bg_task(data, db_path, api_call):
    if api_call == "sendToPurchaseReq":
        processed_data = process_purchase_data(data)
        table =  "purchase_requests" # Data first needs to be entered into purchase_req before sent to approvals
        
        # Insert data into db
        db.insertData(processed_data, table)
        print(f"Data processed into {table}: {processed_data}")

    elif api_call == "getApproveData":
        data = getApprovalData()
        print(f"Fetched approval data: {data}")
        
    elif api_call == "insertApprovalData":
        processed_data = processApprovalsData(data)
        db.insertData(processed_data, "approvals")
        print(f"Data processed into approvals: {processed_data}")        

##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    app.run(debug=True)
    
    
        
    
        
    