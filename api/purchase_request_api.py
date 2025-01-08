from database_manager import DatabaseManager
from notification_manager import NotificationManager
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import json
import os
import pdb
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
link = "http://localhost:5173/approvals-table"
processed_data_shared = None
db_path = os.path.join(os.path.dirname(__file__), "db", "purchase_requests.db")
executor = ThreadPoolExecutor(max_workers=5)

#########################################################################
## EMAIL FIELDS for notifications
to_recipient = "roman_campbell@lawb.uscourts.gov"
from_recipient = "Purchase Request"
this_subject = "Purchase Request Notification"

notifyManager = NotificationManager(msg_body=None, 
                                    to_recipient=to_recipient, 
                                    from_sender=from_recipient, 
                                    subject=this_subject)

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
app = Flask(__name__)
CORS(app)

##########################################################################
## SEND TO APPROVALS -- being sent from the purchase req submit
@app.route('/sendToPurchaseReq', methods=['POST'])
def setPurchaseRequest():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Submit the task to thread executor
    executor.submit(purchase_bg_task, data, "sendToPurchaseReq")
    executor.submit(purchase_bg_task, data, "insertApprovalData")
    
    return jsonify({"message": "Processing started in background"})
    
##########################################################################
## GET APPROVAL DATA
@app.route('/getApprovalData', methods=['GET'])
def getApprovalData():
    try:
        query = "SELECT * FROM approvals"
        approval_data = dbManager.fetch_rows(query)
        return jsonify({"approval_data": approval_data})
    
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
        print("PROCESSING DATA")
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
    
    ##########################################################################
    ## SENDING NOTIFICATION OF NEW REQUEST
    # Create email body and send to approver
    purchase_cols['link'] = link
    email_template = notifyManager.load_email_template("./notification_template.html")
    email_body = email_template.format(**purchase_cols)
    notifyManager.send_email(email_body)
    del purchase_cols['link']
                    
    return approvals_cols

##########################################################################
## GET STATUS OF APPROVALS
def getApprovalStatus(table, req_id):
    condition = f"req_id = %s"
    columns = "approved"
    table = "approvals"
    params = (req_id,)
    dbManager.fetch_single_row(table, columns, condition, params)

##########################################################################
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
def purchase_bg_task(data, api_call):
    try:
        print(f"Background task {api_call} data: {data}")
        if api_call == "sendToPurchaseReq":
            processed_data = processPurchaseData(data)
            table = "purchase_requests" # Data first needs to be entered into purchase_req before sent to approvals
            
            # Insert data into db
            dbManager.insert_data(processed_data, table)
            
            # Send to Approvals table as well
            approval_data = processApprovalsData(processed_data)
            if processed_data['new_request'] == 1:
                approval_data['status'] = "NEW REQUEST"
                processed_data['new_request'] = 0
                
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
    # Create approvals and purchase req tables if not already created
    dbManager = DatabaseManager(db_path)
    
    dbManager.create_purchase_req_table()
    dbManager.create_approvals_table()
    
    # Run Flask
    app.run(debug=True)
    