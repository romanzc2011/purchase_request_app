from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import purchase_request_database as db
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
    'quantity': None
}

##########################################################################
## API FUNCTIONS
##########################################################################

##########################################################################
## SEND TO APPROVALS -- being sent from the purchase req submit
@app.route('/sendToApprovals', methods=['POST'])
def getPurchaseRequest():
    if request.method == 'POST':
        data = request.json
        
        if not data:
            return jsonify({'error': 'Invalid data'}), 400
        
        # Start thread
        thread = threading.Thread(target=purchase_bg_task, args=(data,db_path,"sendToApprovals"))
        thread.start()
        
        return jsonify({"message": "Processing started in background"})
    
##########################################################################
## GET APPROVAL DATA
@app.route('/getApprovalData', methods=['GET'])
def getApprovalData():
    try:
        # Fetch data
        connection = db.getDBConnection(db_path)
        db.createApprovalsTbl(connection)
        
        cursor = connection.cursor()
        query = "SELECT * FROM approvals"
        cursor.execute(query)
        
        # Fetch rows
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        return jsonify(data),  200
    
    except Exception as e:
        print(f"Error fetching approval data: {e}")
        return jsonify({"error": "Failed to fetch data"}), 500
    
    finally:
        connection.close()
    
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
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
def purchase_bg_task(data, db_path, api_call):
    global processed_data_shared
    
    if api_call == "sendToApprovals":
        processed_data = process_purchase_data(data)
        
        # Update shared data
        with lock:
            processed_data_shared = processed_data
            
        for k, v in processed_data.items():
            print(f"{k}: {v}")
        
        # Start new thread to insert data into db
        insert_thread = threading.Thread(target=db.insertPurchaseReq, args=(processed_data,))
        insert_thread.start()
    
    elif  api_call ==  "getApproveData":
        fetch_approve_thread =  threading.Thread(target=getApprovalData, args=(db_path,))
        fetch_approve_thread.start()

##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    app.run(debug=True)
    
    
        
    
        
    