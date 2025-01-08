from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import json
import os
import pdb
import pickle
import purchase_request_database as db
import purchase_request_email as pe
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
link = "http://localhost:5173/approvals-table"
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
    'requester': None,
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
## INIT TABLES
def init_tables():
    connection = db.getDBConnection(db_path)
    db.createPurchaseReqTbl(connection)
    db.createApprovalsTbl(connection)
    connection.close()
    
##########################################################################
## SEND TO APPROVALS -- being sent from the purchase req submit
@app.route('/sendToPurchaseReq', methods=['POST'])
def setPurchaseRequest():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Submit the task to thread executor
    executor.submit(purchase_bg_task, data, db_path, "sendToPurchaseReq")
    executor.submit(purchase_bg_task, data, db_path, "insertApprovalData")
    
    return jsonify({"message": "Processing started in background"})
    
##########################################################################
## GET APPROVAL DATA
@app.route('/getApprovalData', methods=['GET'])
def getApprovalData():
    try:
        data = fetchApprovalData()
        print(f"{data}")
        return jsonify({"approval_data": data})
    except Exception as e:
        print(f"Error fetching approval data: {e}")
        return jsonify({"error": "Failed to  fetch data"}), 500

##########################################################################
## PROGRAM FUNCTIONS
##########################################################################

##########################################################################
## PROCESS PURCHASE DATA
def processPurchaseData(data):
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
## PROCESS APPROVAL DATA --- send new request to approvals
def processApprovalsData(data):
    
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    approved = None
    
    # Is this a new request or has it been approved already
    if purchase_cols['new_request'] == 1:
        approvals_cols['status'] == "NEW REQUEST"
        pe.sendNewNotification()
        
    # Not new? Was it approved or denied?
    elif purchase_cols['new_request'] == 0:
        approved = getApprovalStatus("approvals", data['req_id'])
        if approved == 1:
            approvals_cols['status'] = "APPROVED"
        if approved == 0:
            approvals_cols['status'] = "DENIED"
    
    # Populate approval data 
    with lock:
        for k, v in purchase_cols.items():
            if k in approvals_cols:
                approvals_cols[k] = v
                    
    return approvals_cols

##########################################################################
## GET STATUS OF APPROVALS
def getApprovalStatus(table, req_id):
    query = """SELECT approved FROM ?
               WHERE req_id = ?
            """
    connection = db.getDBConnection(db_path)
    cursor = connection.cursor()
    cursor.execute(query, (table, req_id))
    
##########################################################################
## GET STATUS OF APPROVALS
def fetchApprovalData():
    query = "SELECT * FROM approvals"
    connection = db.getDBConnection(db_path)
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Convert rows to a list of dictionaries
    column_names = [desc[0] for desc in cursor.description] # Get column names
    result = [dict(zip(column_names, row)) for row in rows] # Map colmns->rows
    
    connection.close()
    
    return result
    
##########################################################################
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
def purchase_bg_task(data, db_path, api_call):

    try:
        
        
        print(f"Background task {api_call} data: {data}")
        if api_call == "sendToPurchaseReq":
            processed_data = processPurchaseData(data)
            table = "purchase_requests" # Data first needs to be entered into purchase_req before sent to approvals
            
            # Insert data into db
            db.insertData(processed_data, table)

            # Send to Approvals table as well
            approval_data = processApprovalsData(processed_data)
            if processed_data['new_request'] == 1:
                approval_data['status'] = "NEW REQUEST"
                processed_data['new_request'] = 0
                print(f"APPROVAL DATA: {approval_data}")
                
                # Update the purchase_req table
                updated_data = {'new_request': 0}
                condition = f"req_id = {processed_data['req_id']}"
                db.updateDB(updated_data, table, condition)
                
            table = "approvals"
            db.insertData(approval_data, table)
            
    except Exception as e:
        print(f"Error in background task {api_call}: {e}")
        
##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    init_tables()
    app.run(debug=True)