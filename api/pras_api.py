from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException, status, UploadFile, File, Form, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from cachetools import TTLCache, cached
import uvicorn
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import os, threading, time, uuid, json
from loguru import logger
from dotenv import load_dotenv, find_dotenv
from multiprocessing.dummy import Pool as ThreadPool
from sqlalchemy.orm import Session
from typing import Optional, List
from werkzeug.utils import secure_filename
import services.db_service as dbas
import pydantic_schemas as ps
import jwt  # PyJWT
from jwt.exceptions import ExpiredSignatureError, PyJWTError

from services.auth_service import AuthService
from services.db_service import get_session
from services.email_service import EmailService
from services.ipc_service import IPC_Service
from services.ldap_service import LDAPService, User
from services.search_service import SearchService
from managers.ipc_manager import ipc_instance


"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PRAS - (Purchase Request Approval System)
Will be used to keep track of purchase requests digitally through a central UI. This is the backend that will service
for the UI. When making a purchase request, user will use the their AD username for requestor/recipient.

TO LAUNCH SERVER:
uvicorn pras_api:app --port 5004
"""

# Load environment variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# Config variables
UPLOAD_FOLDER = os.path.join(os.getcwd(), os.getenv("UPLOAD_FOLDER", "uploads"))
LDAP_SERVER = os.getenv("LDAP_SERVER")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
LDAP_SERVICE_USER = os.getenv("LDAP_SERVICE_USER", "ADU\\service_account")
LDAP_SERVICE_PASSWORD = os.getenv("LDAP_SERVICE_PASSWORD", "")
db_path = os.path.join(os.path.dirname(__file__), "db", "purchase_request.db")

# Initialize FastAPI app
app = FastAPI(title="PRAS API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service managers
ldap_svc = LDAPService(
    server_name=LDAP_SERVER,
    port=int(os.getenv("LDAP_PORT")),
    using_tls=os.getenv("LDAP_USE_TLS"),
    service_user=LDAP_SERVICE_USER,
    service_password=LDAP_SERVICE_PASSWORD,
    it_group_dns=os.getenv("IT_GROUP_DNS", "False").lower() == "true",
    cue_group_dns=os.getenv("CUE_GROUP_DNS", "False").lower() == "true",
    access_group_dns=os.getenv("ACCESS_GROUP_DNS", "False").lower() == "true"
)
search_svc = SearchService()
email_svc = EmailService(
    from_sender="Purchase Request", 
    subject="Purchase Request Notification"
)

# Set the recipient emails
email_svc.set_first_approver("Roman Campbell", "roman_campbell@lawb.uscourts.gov")
email_svc.set_final_approver("Roman Campbell", "roman_campbell@lawb.uscourts.gov")

db_svc = next(get_session())  # Initialize with a session
ipc_svc = IPC_Service()
auth_svc = AuthService()

# Thread safety
lock = threading.Lock()

# OAuth2 scheme for JWT token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# User caching
_user_cache = TTLCache(maxsize=1000, ttl=3600)  # user cache
@cached(_user_cache)
def fetch_user(username: str) -> User:
    connection = ldap_svc.get_connection()
    if connection is None:
        logger.warning(f"LDAP connection is None for user {username}, using default user object")
        return User(username=username, email="unknown", group=[])
        
    groups = ldap_svc.check_user_membership(connection, username)
    email = ldap_svc.get_email_address(connection, username)
    
    return ldap_svc.build_user_object(username, groups, email)

# Define get_current_user function
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Verify JWT token
        username = auth_svc.verify_jwt_token(token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no username found"
            )
            
        # Get user email from LDAP
        user_email = ldap_svc.get_email_address(ldap_svc.get_connection(), username)
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: user not found in LDAP"
            )
            
        # Get user groups from LDAP
        user_groups = ldap_svc.get_groups()
        if not user_groups:
            logger.warning(f"No groups found for user {username}")
            user_groups = []
            
        user = User(
            username=username,
            email=user_email,
            group=user_groups
        )
        return user
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except PyJWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except HTTPException:
        # Re-raise HTTP exceptions (including our custom ones)
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing authentication"
        )

# API router
api_router = APIRouter(prefix="/api", tags=["API Endpoints"])

##########################################################################
## LOGIN -- auth users and return JWTs
@api_router.post("/login")
async def login(credentials: dict):
    username = credentials.get("username")
    password = credentials.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")
    
    adu_user = f"ADU\\{username}"
    connection = ldap_svc.create_connection(adu_user, password)
    
    if connection is None:
        logger.error(f"LDAP authentication failed for user {username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    try:
        user = fetch_user(username)
        access_token = auth_svc.create_access_token(identity=username)
        refresh_token = auth_svc.create_access_token(identity=username, expires_delta=timedelta(days=7))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }
    except Exception as e:
        logger.error(f"Error in login: {e}")
        raise HTTPException(status_code=500, detail="Login error")

##########################################################################
## GET APPROVAL DATA
@api_router.get("/getApprovalData", response_model=List[ps.AppovalSchema])
async def get_approval_data(current_user: User = Depends(get_current_user)):
    session = next(get_session())
    try:
        approval = dbas.get_all_approval(session)
        approval_data = [ps.AppovalSchema.model_validate(approval) for approval in approval]
        return approval_data
    finally:
        session.close()

##########################################################################
## GET SEARCH DATA
@api_router.get("/getSearchData/search", response_model=List[ps.AppovalSchema])
async def get_search_data(
    query: str = "",
    column: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # If column is provided, use _exact_singleton_search instead
    if column:
        results = search_svc._exact_singleton_search(column, query, db=None)
    else:
        # Otherwise use the standard execute_search method
        results = search_svc.execute_search(query, db=None)
    
    return JSONResponse(content=jsonable_encoder(results))

##########################################################################
## SEND TO approval -- being sent from the purchase req submit
@api_router.post("/sendToPurchaseReq")
async def set_purchase_request(data: dict, current_user: str = Depends(get_current_user)):
    logger.info(f"Authenticated user: {current_user}")
    if not data:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    from multiprocessing.dummy import Pool as ThreadPool
    pool = ThreadPool()
    
    # Extract requester 
    requester = data.get("requester")
    ldap_svc.set_requester(requester)
    if not requester:
        logger.error(f"Requester not found in data: {data}")
        raise HTTPException(status_code=400, detail="Invalid requester")
    # Log the requester
    logger.info(f"REQUESTER: {requester}")
    
    # Get requester email address
    requester_email = ldap_svc.get_email_address(ldap_svc.get_connection(), requester)
    if not requester_email: 
        logger.error(f"Could not find email for user {requester}")
        raise HTTPException(status_code=400, detail="Invalid requester")
    # Set the email service requester
    email_svc.set_requester(requester, requester_email);
    
    ## Verify that requester is a legitimate user in AD via ldap
    # Ensure we have a valid LDAP connection
    if not ldap_svc.check_ldap_connection(current_user):
        # Try to establish a new connection using service account
        conn = ldap_svc.create_connection(LDAP_SERVICE_USER, LDAP_SERVICE_PASSWORD)
        if conn is None:
            logger.warning(f"Could not establish LDAP connection for user verification")
        else:
            # Check if the requester is a legitimate user
            is_legitimate = ldap_svc.check_legitimate_user(conn, requester)
            if not is_legitimate:
                logger.error(f"Requester {requester} is not a legitimate user in AD")
                raise HTTPException(status_code=400, detail="Invalid requester")
    else:
        # Get LDAP connection
        conn = ldap_svc.get_connection()
        # Check if the requester is a legitimate user
        is_legitimate = ldap_svc.check_legitimate_user(conn, requester)
        if not is_legitimate:
            logger.error(f"Requester {requester} is not a legitimate user in AD")
            raise HTTPException(status_code=400, detail="Invalid requester")
    
    # Get user info - this already includes the email address
    user_info = fetch_user(requester)
    logger.info(f"USER INFO: {user_info}")

    processed_data = pool.map(process_purchase_data, [data])
    copied_data = processed_data[0].copy()  # or use deepcopy if needed
    pool.map(purchase_req_commit, [copied_data])
    pool.close()
    pool.join()
        
    return JSONResponse(content={"message": "Processing started in background"})
    
##########################################################################
## DELETE PURCHASE REQUEST table, condition, params
@api_router.post("/deleteFile")
async def delete_file(data: dict, current_user: str = Depends(get_current_user)):
    """
    Deletes a file given its ID and filename.
    Expects a JSON payload containing "ID" and "filename".
    """
    if not data:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    ID = data.get("ID")
    filename = data.get("filename")
    if not ID or not filename:
        raise HTTPException(status_code=400, detail="Missing ID or filename")
    
    # Construct the upload filename
    upload_filename = f"{ID}_{filename}"
    files = os.listdir(UPLOAD_FOLDER)
    file_found = False
    
    for file in files:
        if file == upload_filename:
            logger.info(f"Deleting file: {os.path.join(UPLOAD_FOLDER, upload_filename)}")
            os.remove(os.path.join(UPLOAD_FOLDER, file))
            file_found = True
            break

    if not file_found:
        raise HTTPException(status_code=404, detail="File not found")

    return {"delete": True}
    
##########################################################################
## HANDLE FILE UPLOAD
@api_router.post("/upload")
async def upload_file(ID: str = Form(...), file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    # Ensure the upload directory exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    try:
        secure_name = secure_filename(file.filename)
        new_filename = f"{ID}_{secure_name}"
        file_path = os.path.join(UPLOAD_FOLDER, new_filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"File saved: {file_path}")
        return JSONResponse(content={"message": "File uploaded successfully", "filename": new_filename})
    except Exception as e:
        logger.error(f"Error during file upload: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

#########################################################################
## LOGGING FUNCTION - for middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)
    elapsed = time.time() - start_time
    logger.bind(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        status_code=response.status_code,
        elapsed=elapsed,
    ).info("Request processed")
    response.headers["X-Request-ID"] = request_id
    return response

#########################################################################
## GET REQ ID -- send back to caller
@api_router.post("/getReqID")
async def get_req_id(data: dict = None, current_user: str = Depends(get_current_user)):
    if data is None:
        data = {}
    req_id = create_req_id(data)
    logger.success("Requisition id created.")
    return JSONResponse(content={"reqID": req_id})

##########################################################################
## APPROVE/DENY PURCHASE REQUEST
@api_router.post("/approveDenyRequest")
async def approve_deny_request(data: dict, current_user: User = Depends(get_current_user)):
    try:
        request_id = data.get("request_id")
        action = data.get("action")
        
        if not request_id or not action:
            raise HTTPException(status_code=400, detail="Missing request_id or action")
            
        # Get current status
        current_status = dbas.get_status_by_id(request_id)
        if not current_status:
            raise HTTPException(status_code=404, detail="Request not found")
            
        # Process based on current status
        if current_status == "NEW REQUEST":
            if action.lower() == "approve":
                new_status = "PENDING"
                dbas.update_data(request_id, "approval", status=new_status)
                email_svc.set_request_status("NEW REQUEST")
                email_svc.send_notification(
                    template_path="./templates/approval_notification.html",
                    template_data={"request_id": request_id, "action": "approved"},
                    subject="Purchase Request Approved"
                )
            elif action.lower() == "deny":
                new_status = "DENIED"
                dbas.update_data(request_id, "approval", status=new_status)
                email_svc.set_request_status("NEW REQUEST")
                email_svc.send_notification(
                    template_path="./templates/denial_notification.html",
                    template_data={"request_id": request_id, "action": "denied"},
                    subject="Purchase Request Denied"
                )
        elif current_status == "PENDING":
            if action.lower() == "approve":
                new_status = "APPROVED" 
                dbas.update_data(request_id, "approval", status=new_status)
                # Send email to final approver
                email_svc.set_request_status("PENDING")
                email_svc.send_notification(
                    template_path="./templates/final_approval_notification.html",
                    template_data={"request_id": request_id, "action": "approved"},
                    subject="Purchase Request Final Approval"
                )
                # Send email to current user (approver)
                email_svc.set_request_status("PENDING")
                email_svc.send_notification(
                    template_path="./templates/approval_notification.html",
                    template_data={"request_id": request_id, "action": "approved"},
                    subject="Purchase Request Approved"
                )
                # Send email to requester
                requester_email = dbas.get_requester_email(db_svc, request_id)
                if requester_email:
                    email_svc.set_request_status("PENDING")
                    email_svc.send_notification(
                        template_path="./templates/approval_notification.html",
                        template_data={"request_id": request_id, "action": "approved"},
                        subject="Purchase Request Approved"
                    )
            elif action.lower() == "deny":
                new_status = "DENIED"
                dbas.update_data(request_id, "approval", status=new_status)
                email_svc.set_request_status("PENDING")
                email_svc.send_notification(
                    template_path="./templates/denial_notification.html",
                    template_data={"request_id": request_id, "action": "denied"},
                    subject="Purchase Request Denied"
                )
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'deny'")
        
        return {"status": "success", "message": f"Request {action.lower()}ed successfully"}
    except Exception as e:
        logger.error(f"Error in approve/deny request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

##########################################################################
## REFRESH TOKEN
@api_router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        # Verify the refresh token
        username = auth_svc.verify_jwt_token(refresh_token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
        # Create new access token
        new_access_token = auth_svc.create_access_token(identity=username)
        
        return {
            "access_token": new_access_token
        }
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token"
        )

##########################################################################
##########################################################################
## PROGRAM FUNCTIONS -- non API
##########################################################################
##########################################################################

app.include_router(api_router)

##########################################################################
## PROCESS PURCHASE DATA
def process_purchase_data(data):
    with lock:
        logger.success(f"priceEach {data['priceEach']}")
        local_purchase_cols = {col.name: None for col in dbas.PurchaseRequest.__table__.columns}
        try:
            for k, v in data.items():
                if k in local_purchase_cols:
                    local_purchase_cols[k] = v
                    
            if 'learnAndDev' in local_purchase_cols:
                local_purchase_cols['trainNotAval'] = local_purchase_cols['learnAndDev'].get('trainNotAval', False)
                local_purchase_cols['needsNotMeet'] = local_purchase_cols['learnAndDev'].get('needsNotMeet', False)
                del local_purchase_cols['learnAndDev']
                
            if 'priceEach' in local_purchase_cols and 'quantity' in local_purchase_cols:
                
                try:
                    print(local_purchase_cols['priceEach'])
                    local_purchase_cols['priceEach'] = float(local_purchase_cols['priceEach'])
                    local_purchase_cols['quantity'] = int(local_purchase_cols['quantity'])
                    if local_purchase_cols['priceEach'] < 0 or local_purchase_cols['quantity'] <= 0:
                        raise ValueError("Invalid values")
                    local_purchase_cols['totalPrice'] = round(local_purchase_cols['priceEach'] * local_purchase_cols['quantity'], 2)
                    logger.success(f"TOTAL: {local_purchase_cols['totalPrice']}")
                    
                except ValueError as e:
                    logger.error("Invalid price or quantity:")
                    local_purchase_cols['totalPrice'] = 0
                    
            local_purchase_cols['newRequest'] = True
            local_purchase_cols['pendingApproval'] = False
            local_purchase_cols['approved'] = False
            
        except Exception as e:
            logger.error(f"Error in process_purchase_data: {e}")
            
    return local_purchase_cols

##########################################################################
## GENERATE REQUISITION ID
def create_req_id(processed_data):
    requester_part = processed_data.get('requester', '')[:4]
    boc_part = processed_data.get('budgetObjCode', '')[:4]
    fund_part = processed_data.get('fund', '')[:4]
    location_part = processed_data.get('location', '')[:4]
    id_part = processed_data.get('ID', '')[9:13]  # Adjust if needed
    return f"{requester_part}-{boc_part}-{fund_part}-{location_part}-{id_part}"

##########################################################################
## UPDATE REQUEST STATUS
def update_request_status(id, status):
    # Send a message to EmailService via IPC
    message_content = {
        "id": id,
        "status": status
    }
    ipc_instance.send_message(
        content=message_content,
        msg_type="REQUEST_STATUS_UPDATE"
    )
    logger.info(f"Request status updated: {id} to {status}")

##########################################################################
## PROCESS APPROVAL DATA --- send new request to approval
def process_approval_data(processed_data):
    print("PROCESSED: ", processed_data)
    logger.info(f"Processing approval data: {processed_data}")
    
    pendingApproval = False
    approval_data = {}
    
    if not isinstance(processed_data, dict):
        raise ValueError("Data must be a dictionary")
    
    # Determine approval status via status
    if processed_data.get('newRequest'):
        approval_data['status'] = "NEW REQUEST"
        
    elif processed_data.get('pendingApproval'):
        approval_data['status'] = "PENDING"
        
    elif (not processed_data.get('newRequest') and
          not processed_data.get('pendingApproval') and
          not processed_data.get('approved')):
        approval_data['status'] = "DENIED"
        
    else:
        approval_data["status"] = "UNKNOWN"
    
    # Define allowed keys that correspond to the Approval model's columns.
    allowed_keys = [
        'ID', 'reqID', 'requester', 'recipient', 'budgetObjCode',  'fund', 
        'itemDescription', 'justification', 'quantity', 'totalPrice', 'priceEach', 'location', 
        'newRequest', 'pendingApproval', 'approved'
    ]
    
    # Populate approval_data from processed_data
    for key, value in processed_data.items():
        if key in allowed_keys:
            approval_data[key] = value
            
    ##########################################################################
    ## SENDING NOTIFICATION OF NEW REQUEST
    # Create email body and send to approver
    logger.info("Sending notification email to approver...")
    logger.info(f"Request status before sending notification: {approval_data['status']}")
    email_svc.send_notification(
        template_data=processed_data,
        subject="New Purchase Request",
        request_status=approval_data['status']
    )
                    
    return approval_data

##########################################################################
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
def purchase_req_commit(processed_data):
    with lock:
        try:
            table = "purchase_request"
            # Get a session and use it directly
            session = next(get_session())
            try:
                
                dbas.insert_data(processed_data, table)
                session.commit()
                
                approval_data = process_approval_data(processed_data)
                logger.info(f"newRequest: {processed_data.get('newRequest')}")
                
                if processed_data.get('newRequest') == 1:
                    approval_data['status'] = "NEW REQUEST"
                    table = "approval"
                    # Call insert data
                    dbas.insert_data(approval_data, table)
                    session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Exception occurred: {e}")

##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    uvicorn.run("pras_api:app", host="localhost", port=5004, reload=True)