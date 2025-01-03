from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import threading

db_path = os.path.join(os.path.dirname(__file__), "db", "pruchases.db")

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
    'learnAndDev': None,
    'budgetObjCode': None,
    'fund': None,
    'price': None,
    'location': None,
    'quantity': None
}

@app.route('/sendData', methods=['POST'])
def getPurchaseRequest():
    if request.method == 'POST':
        data = request.json
        
        if not data:
            return jsonify({"error": "Invalid data"}), 400  
    
    for item in data['dataBuffer']:
        if isinstance(item, dict):
            for k,v in item.items():
                print(f"{k}: {v}")
                
    return jsonify(data)
       
    
if __name__ == "__main__":
    app.run(debug=True)
    data = getPurchaseRequest() 
    
        
    
        
    