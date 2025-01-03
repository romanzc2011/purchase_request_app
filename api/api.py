import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import request
import os

db_path = os.path.join(os.path.dirname(__file__), "db", "pruchases.db")

app = Flask(__name__)
CORS(app)

@app.route('/sendData', methods=['POST'])
def addPurchaseRequest():
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({"error": "Invalid data"}), 400

    # Break data up into variables
    id = data.get("id")
    requester = data.get("requester")
    phone_ext = data.get("phone_ext")
    date_request = data.get("date_request")
    date_needed = data.get("date_needed")
    order_type = data.get("order_type")
    file_attachments = data.get("file_attachments")
    item_description = data.get("item_description")
    justification = data.get("justification")
    addition_comments = data.get("addition_comments")
    training_not_aval = data.get("training_not_aval")
    needs_not_meet = data.get("needs_not_meet")
    budget_obj_code = data.get("budget_obj_code")
    fund = data.get("fund")
    price = data.get("price")
    location = data.get("location")
    quantity = data.get("quantity")

if __name__ == "__main__":
    app.run(debug=True)