from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import threading

"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PURCHASE REQUEST APP
Will be used to keep track of purchase requests digitally through a central UI. This is the backend that will service
the UI.
"""

db_path = os.path.join(os.path.dirname(__file__), "db", "purchase_requests.db")
lock = threading.Lock()

app = Flask(__name__)
CORS(app)

# Dictionary for sql column
purchase_cols = {
    'id': None,
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
@app.route('/getPurchaseData', methods=['POST'])
def getPurchaseRequest():
    if request.method == 'POST':
        data = request.json
        
        if not data:
            return jsonify({'error': 'Invalid data'}), 400
        
        # Start thread
        thread = threading.Thread(target=purchase_bg_task, args=(data,))
        thread.start()
        
        return jsonify({"message": "Processing started in background"})

##########################################################################
## PROGRAM FUNCTIONS
##########################################################################
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
        
    return purchase_cols

# Purchase col background thread
def purchase_bg_task(data):
    processed_data = process_purchase_data(data)
    
    for k, v in processed_data.items():
        print(f"{k}: {v}")

##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    app.run(debug=True)
    
    
        
    
        
    