from multiprocessing import process
from re import search
from adu_ldap_manager import LDAPManager
from search_service import SearchService
from constants.db_columns import purchase_cols
from constants.db_columns import approvals_cols
from copy import deepcopy
from datetime import (datetime, timedelta, timezone)
from pras_database_manager import DatabaseManager
from dotenv import load_dotenv, set_key, find_dotenv
from flask_cors import CORS, cross_origin
from flask import Flask, request, jsonify, Response, g, make_response
from flask_jwt_extended import (create_access_token,
                                create_refresh_token, 
                                get_jwt,
                                get_jwt_identity, 
                                jwt_required, 
                                JWTManager, 
                                set_access_cookies,
                                unset_jwt_cookies)
from ldap3.core.exceptions import LDAPBindError
from loguru import logger
from multiprocessing.dummy import Pool as ThreadPool
from notification_manager import NotificationManager
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from search_service import SearchService

import json
import os
import psutil
import threading
import time
import uuid

"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PRAS - (Purchase Request Approval System)
Will be used to keep track of purchase requests digitally through a central UI. This is the backend that will service
for the UI. 
"""

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
UPLOAD_FOLDER = os.path.join(os.getcwd(), os.getenv("UPLOAD_FOLDER", "uploads"))
LDAP_SERVER = os.getenv("LDAP_SERVER")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
lock = threading.Lock()
processed_data_shared = None
db_path = os.path.join(os.path.dirname(__file__), "db", "purchase_requests.db")
search_service = SearchService()

#########################################################################
## APP CONFIGS
pras = Flask(__name__)
CORS(pras, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Configure Loguru
logger.add("./logs/pras.log", diagnose=True, rotation="7 days")

pras.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024   # 16MB
pras.config["SECRET_KEY"] = JWT_SECRET_KEY
pras.config["JWT_TOKEN_LOCATION"] = ["headers"]
pras.config["JWT_ACCESS_COOKIE_PATH"] = "/"
#pras.config["JWT_COOKIE_SECURE"] = True  # Cookies will only be sent via HTTPS
pras.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(pras)

#########################################################################
## EMAIL FIELDS for notifications
to_recipient = "roman_campbell@lawb.uscourts.gov"
from_recipient = "Purchase Request"
this_subject = "Purchase Request Notification"

notifyManager = NotificationManager(msg_body=None, 
                                    to_recipient=to_recipient, 
                                    from_sender=from_recipient, 
                                    subject=this_subject)

##########################################################################
##########################################################################
## API FUNCTIONS
##########################################################################
##########################################################################

##########################################################################
## LOGIN -- auth users and return JWTs
@pras.route('/api/login', methods=['POST'])
def login():
    
    try:
        username = request.json.get("username", None)
        password = request.json.get("password", None)
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
    
    # Append ADU\ to username to match AD structure
    adu_username = "ADU\\"+username
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    # Connect to LDAPS server and attempt to bind which involves authentication    
    try:
        ldap_mgr = LDAPManager(LDAP_SERVER, 636, True)
        connection = ldap_mgr.get_connection(adu_username, password)
        
        if connection.bound:
            AD_Groups = ldap_mgr.check_user_membership(connection, username)
            access_token = create_access_token(identity=username)
            
            # Create response
            response = jsonify({
                "message": "Login successful",
                "access_token": access_token,
                "AD_Groups": AD_Groups
            })
            
            set_access_cookies(response, access_token)
            
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        
        else:
            return jsonify({"error":" Invalid credentials"}), 401
        
    except LDAPBindError as e:
        return jsonify({"error": "Invalid username or password"}), 401
    
    except Exception as e:
        logger.warning(f"LDAP authentication error: {e}")
        return jsonify({"error": "LDAP authentication failed"}), 500
    
##########################################################################
## LOGOUT
@pras.route("/api/logout", methods=["POST"])
def logout():
    response = jsonify({ "msg": "logout successful" })
    unset_jwt_cookies(response)
    return response
    
##########################################################################
## REFRESH TOKEN
## # Using an `after_request` callback, refresh any token that is within 30 minutes of expiring.
@pras.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        
        if target_timestamp > exp_timestamp:
            logger.info("TOKEN REFRESH")
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case for an invalid JWT
        return response

##########################################################################
## SEND TO APPROVALS -- being sent from the purchase req submit
@pras.route('/api/sendToPurchaseReq', methods=['POST'])
@jwt_required()
def set_purchase_request():
    # Retrieve authenticated user from JWT
    current_user = get_jwt_identity()
    logger.info(f"Authenticated user: {current_user}")
    
    data = request.json
    if not data:
        logger.error("Invalid data")
        return jsonify({'error': 'Invalid data'}), 400
    
    # Process purchase data
    pool = ThreadPool()
    processed_data = pool.map(process_purchase_data, [data])
    
    copied_data = deepcopy(processed_data[0])
    
    pool.map(purchase_req_commit, [copied_data])
    pool.close()
    pool.join()
        
    return jsonify({"message": "Processing started in background"})
    
##########################################################################
## GET APPROVAL DATA
@pras.route('/api/getApprovalData', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_approval_data():

    if request.method == "OPTIONS":
        logger.info(f"{request.method}")
        return jsonify({"status": "OK"})
    try:
        query = "SELECT * FROM approvals"
        approval_data = dbManager.fetch_rows(query)
        
        logger.info(f"APPROVAL DATA: {approval_data}")
        return jsonify({"approval_data": approval_data})
    
    except Exception as e:
        logger.error(f"Error fetching approval data: {e}")
        return jsonify({"error": "Failed to  fetch data"}), 500

##########################################################################
## GET SEARCH DATA
@pras.route('/api/getSearchData', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_search_data():
    query = request.args.get('query', '')
    retval = search_service.get_search_results(query)
    return jsonify(retval)
    
##########################################################################
## DELETE PURCHASE REQUEST table, condition, params
@pras.route('/api/deleteFile', methods=['POST'])
@pras.route('/api/deletePurchaseReq', methods=['GET', 'POST'])
@jwt_required()
def delete_func():
    if request.path == '/api/deleteFile':
        data = request.get_json()

        # Extract ID and filename
        ID = data.get("ID")
        filename = data.get("filename")
        upload_filename = f"{ID}_{filename}"
        
        # Delete File with ID in 
        files = os.listdir(UPLOAD_FOLDER)
        for file in files:
            if file == upload_filename:
                logger.info(f"{UPLOAD_FOLDER}\\{upload_filename}")
                os.remove(os.path.join(UPLOAD_FOLDER, file))
    
    if not data:
        logger.warning("Invalid data")
        return jsonify({"error": "Invalid data"}), 400
    
    
    return jsonify({"delete": True}), 200
    
##########################################################################
## HANDLE FILE UPLOAD
@pras.route('/api/upload', methods=['POST', 'OPTIONS'])
@jwt_required()
def upload_file():
    if request.method == 'OPTIONS':
        return '', 200
    
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    ID = request.form.get("ID")
    saved_files = []

    # Ensure the upload directory exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    try:
        uploaded_files = request.files.getlist("file")
        for file in uploaded_files:
            if file.filename:
                secure_name = secure_filename(file.filename)
                new_filename = f"{ID}_{secure_name}"
                file_path = os.path.join(UPLOAD_FOLDER, new_filename)
                file.save(file_path)
                saved_files.append(file.filename)

                logger.info(f"UPLOAD_FOLDER resolved to: {UPLOAD_FOLDER}")
    except Exception as e:
        logger.error(f"Error during file upload: {e}")
        return jsonify({"error": "File upload failed", "details": str(e)}), 500
    
    return jsonify({"message": "File(s) uploaded successfully", "files": saved_files, "ID": ID}), 200

#########################################################################
## LOGGING FUNCTION - for middleware
@pras.after_request
@logger.catch()
def logging_middleware(response):
    request_id = str(uuid.uuid4())
    
    with logger.contextualize(request_id=request_id):
        elapsed = time.time() - getattr(request, "start_time", time.time())
        
        logger.bind(
            path=request.path,
            method=request.method,
            status_code=response.status_code,
            response_size=len(response.get_data()),
            elapsed=elapsed,
        ).info("incoming '{method}' to '{path}'",method = request.method, path=request.path)
        
        response.headers["X-Request-ID"] = request_id
        
    return response

#########################################################################
## GET REQ ID -- send back to caller
@pras.route('/api/getReqID', methods=['POST'])
@jwt_required()
def get_req_id():
    data = request.get_json() or {}
    req_id = create_req_id(data)
    logger.success('Requisition id created.')
    return jsonify({'reqID': req_id})

##########################################################################
##########################################################################
## PROGRAM FUNCTIONS -- non API
##########################################################################
##########################################################################

##########################################################################
## PROCESS PURCHASE DATA
def process_purchase_data(data):
    with lock:
        local_purchase_cols = purchase_cols.copy()
        logger.info(f"Processing data: {data}")
                
        try:
            # Populate local_purchase_cols with appropriate data from api call
            for k, v in data.items():
                if k in local_purchase_cols:
                    local_purchase_cols[k] = v
                        
            # Extract the learnAndDev element
            if 'learnAndDev' in local_purchase_cols:
                local_purchase_cols['trainNotAval'] = local_purchase_cols['learnAndDev'].get('trainNotAval', False)
                local_purchase_cols['needsNotMeet'] = local_purchase_cols['learnAndDev'].get('needsNotMeet', False)
                del local_purchase_cols['learnAndDev']
            
            # Calc and separate price of each and total
            if 'price' in local_purchase_cols and 'quantity' in local_purchase_cols:
                try:
                    local_purchase_cols['priceEach'] = float(local_purchase_cols['price'])
                    local_purchase_cols['quantity'] = int(local_purchase_cols['quantity'])
                    
                    # Validate ranges
                    if local_purchase_cols['priceEach'] < 0 or local_purchase_cols['quantity'] <= 0:
                        raise ValueError("Price must be non-negative, and quantity must be greater than zero.")
                    
                    # Calculate totalPrice
                    local_purchase_cols['totalPrice'] = round(local_purchase_cols['priceEach'] * local_purchase_cols['quantity'], 2)
                    
                except ValueError as e:
                    logger.error("Invalid price or quantity:")
                    local_purchase_cols['totalPrice'] = 0
                del local_purchase_cols['price']
        
            # Show this is a new request 0=FALSE 1=TRUE
            local_purchase_cols['new_request'] = 1
            local_purchase_cols['approved'] = 0

            logger.info(f"Heres reqID: {local_purchase_cols['reqID']}")

        except Exception as e:
            logger.error(f"Error in process_purchase_data: {e}")
        
    return local_purchase_cols

##########################################################################
## GENERATE REQUISITION ID
def create_req_id(processed_data):
    requester_part = processed_data.get('requester', '')[:4]
    boc_part = processed_data.get('budgetObjCode', '').split("-")[0][:4]
    fund_part = processed_data.get('fund', '')[:4]
    location_part = processed_data.get('location', '')[:4]
    id_part = processed_data.get('ID', '')[9:13]  # first 4 char length of uuid

    return f"{requester_part}-{boc_part}-{fund_part}-{location_part}-{id_part}"

##########################################################################
## PROCESS APPROVAL DATA --- send new request to approvals
def process_approvals_data(processed_data):
    logger.info(f'LINE 340 - process_approvals_data: {processed_data}')
    
    if not isinstance(processed_data, dict):
        raise ValueError("Data must be a dictionary")
    
    # Is this a new request or has it been approved already
    if processed_data['new_request'] == 1:
        approvals_cols['status'] = "NEW REQUEST"
        
    # Not new? Was it approved or denied?
    elif purchase_cols['new_request'] == 0:
        approved = get_approval_status("approvals", processed_data['ID'])
        if approved == 1:
            approvals_cols['status'] = "APPROVED"
        if approved == 0:
            approvals_cols['status'] = "DENIED"
    
    # Populate approval data 
    for k, v in processed_data.items():
        if k in approvals_cols:
            approvals_cols[k] = v
            
    ##########################################################################
    ## SENDING NOTIFICATION OF NEW REQUEST
    # Create email body and send to approver
    logger.info("SENDING EMAIL to approver...")
    email_template = notifyManager.load_email_template("./notification_template.html")
    email_body = email_template.format(**processed_data)
    notifyManager.send_email(email_body)
                    
    return approvals_cols

##########################################################################
## GET STATUS OF APPROVALS
def get_approval_status(table, ID):
    condition = f"ID = %s"
    columns = "approved"
    table = "approvals"
    params = (ID,)
    dbManager.fetch_single_row(table, columns, condition, params)

##########################################################################
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
def purchase_req_commit(processed_data):
    with lock:
        
        try:
            # Insert data into db
            table = "purchase_requests" # Data first needs to be entered into purchase_req before sent to approvals
            dbManager.insert_data(processed_data, table)
            
            # Send to Approvals table as well
            approval_data = process_approvals_data(processed_data)
            
            # These are handling new requests, no updating new_request col until either a deny or approve
            logger.info(f"new_request: {processed_data['new_request']}")
            if processed_data['new_request'] == 1:
                approval_data['status'] = "NEW REQUEST"
                table = "approvals"
                dbManager.insert_data(approval_data, table)
                
        except Exception as e:
            logger.error(f"Exception occurred: {e}")
        
##########################################################################
## GET PRIVATE IP from 10.222.0.0/19 or 10.223.0.0/19 network
def get_server_ip(network):
    interfaces = psutil.net_if_addrs()
    
    for interface, addresses in interfaces.items():
        if "Ethernet" in interface:
            for addr in addresses:
                if addr.family == 2: # ipv4 addr (AF_INET)
                    if addr.address.startswith(network):
                        # prasend port 5002 to ip addr
                        ip_addr = addr.address
                        return ip_addr
    # Default fallback
    return "127.0.0.1"
        
##########################################################################
## MAIN FUNCTION -- main function for primary control flow
def main():
    #serve(pras, host="10.234.198.113", port=5004)
    pras.run(host="localhost", port=5004, debug=True)
        
##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    dbManager = DatabaseManager(db_path)
    main()