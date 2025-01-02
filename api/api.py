import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import request

app = Flask(__name__)
CORS(app)

@app.route('/sendData', methods=['POST'])
def sendDataResponse():
    incoming_data = request.get_json()

    print("Incoming Data:", incoming_data)

    # Respond with a success message
    return jsonify({"message": "Data received successfully", "received": incoming_data})


if __name__ == "__main__":
    app.run(debug=True)