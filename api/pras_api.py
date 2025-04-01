from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException, status, UploadFile, File, Form, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import uvicorn
from datetime import datetime, timedelta, timezone
from typing import List
import os, threading, time, uuid, json
from loguru import logger
from dotenv import load_dotenv, find_dotenv
from ldap3.core.exceptions import LDAPBindError
from multiprocessing.dummy import Pool as ThreadPool
from adu_ldap_service import LDAPManager
from search_service import SearchService
from notification_manager import NotificationManager
from sqlalchemy.orm import Session
from typing import Optional, List
from werkzeug.utils import secure_filename
import db_alchemy_service as dbas
import psutil
import pydantic_schemas as ps
import jwt  # PyJWT
import search_service

"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PRAS - (Purchase Request Approval System)
Will be used to keep track of purchase requests digitally through a central UI. This is the backend that will service
for the UI. 

uvicorn pras_api:app --port 5004
"""
# Load environment variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
UPLOAD_FOLDER = os.path.join(os.getcwd(), os.getenv("UPLOAD_FOLDER", "uploads"))
LDAP_SERVER = os.getenv("LDAP_SERVER")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
db_path = os.path.join(os.path.dirname(__file__), "db", "purchase_request.db")

#########################################################################
## APP CONFIGS
app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logger.add("./logs/pras.log", diagnose=True, rotation="7 days")

##########################################################################
# Initialize services and shared objects
notifyManager = NotificationManager(
    msg_body=None, 
    to_recipient="roman_campbell@lawb.uscourts.gov", 
    from_sender="Purchase Request", 
    subject="Purchase Request Notification"
)
lock = threading.Lock()

# OAuth2 scheme placeholder (used to extract JWT token from Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Instantiate search service
searchService = SearchService()
searchService.create_whoosh_index()


##########################################################################
## JWT UTILITY FUNCTIONS
##########################################################################
def create_access_token(identity: str, expires_delta: timedelta = timedelta(hours=1)):
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": identity, "exp": expire}
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return token

## VERIFY JWT TOKEN 
def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


## GET CURRENT USER
async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_jwt_token(token)
    print(user)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user

##########################################################################
##########################################################################
## API ENDPOINTS
##########################################################################
##########################################################################

api_router = APIRouter(prefix="/api", tags=["API Endpoints"])

##########################################################################
## LOGIN -- auth users and return JWTs
@api_router.post("/login")
async def login(credentials: dict):
    # Expecting JSON with username/password
    username = credentials.get("username")
    password = credentials.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")
    
    # Append ADU\ to username to match AD structure
    adu_username = "ADU\\"+username
    
    # Connect to LDAPS server and attempt to bind which involves authentication    
    try:
        ldap_mgr = LDAPManager(LDAP_SERVER, 636, True)
        connection = ldap_mgr.get_connection(adu_username, password)
        
        if connection.bound:
            AD_Groups = ldap_mgr.check_user_membership(connection, username)
            access_token = create_access_token(identity=username)
            
            # Create response
            return JSONResponse(content={
                "message": "Login successful",
                "access_token": access_token,
                "AD_Groups": AD_Groups
            })
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
    except LDAPBindError:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        logger.warning(f"LDAP authentication error: {e}")
        raise HTTPException(status_code=500, detail="LDAP authentication failed")
    
##########################################################################
## LOGOUT
@api_router.post("/logout")
async def logout():
    # In FastAPI, logging out is usually handled on the client side by discarding the token.
    return JSONResponse(content={"msg": "Logout successful"})

##########################################################################
## GET APPROVAL DATA
@api_router.get("/getApprovalData", response_model=List[ps.AppovalSchema])
async def get_approval_data(
    current_user: str = Depends(get_current_user), 
    db: Session = Depends(dbas.get_db_session)
):
    approval = dbas.get_all_approval(db)
    
    # Convert each approval instance to Pydantic instance in foreach
    approval_data = [ps.AppovalSchema.model_validate(approval) for approval in approval]
    return approval_data

##########################################################################
## GET SEARCH DATA
@api_router.get("/getSearchData/search", response_model=List[ps.AppovalSchema])
async def get_search_data(
    query: str = "", 
    column: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(dbas.get_db_session)
):
    logger.info(f"Search for query: {query}")
    
    results = searchService.execute_search(query)
    return JSONResponse(content=jsonable_encoder(results))

##########################################################################
## SEND TO approval -- being sent from the purchase req submit
@api_router.post("/sendToPurchaseReq")
async def set_purchase_request(data: dict, current_user: str = Depends(get_current_user)):
    print("set_purchase_request:", data)
    logger.info(f"Authenticated user: {current_user}")
    if not data:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    from multiprocessing.dummy import Pool as ThreadPool
    pool = ThreadPool()
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
    boc_part = processed_data.get('budgetObjCode', '').split("-")[0][:4]
    fund_part = processed_data.get('fund', '')[:4]
    location_part = processed_data.get('location', '')[:4]
    id_part = processed_data.get('ID', '')[9:13]  # Adjust if needed
    return f"{requester_part}-{boc_part}-{fund_part}-{location_part}-{id_part}"

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
        'ID', 'reqID', 'requester', 'recipient', 'budgetObjCode', 
        'fund', 'quantity', 'totalPrice', 'priceEach', 'location', 
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
    email_template = notifyManager.load_email_template("./notification_template.html")
    email_body = email_template.format(**processed_data)
    notifyManager.send_email(email_body)
                    
    return approval_data

##########################################################################
## GET STATUS OF approval
def get_approval_status(ID):
    condition = dbas.Approval.ID == ID
    columns = [dbas.Approval.approved]

##########################################################################
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
def purchase_req_commit(processed_data):
    with lock:
        try:
            table = "purchase_request"
            dbas.insert_data(processed_data, table)
            approval_data = process_approval_data(processed_data)
            logger.info(f"newRequest: {processed_data.get('newRequest')}")
            
            if processed_data.get('newRequest') == 1:
                approval_data['status'] = "NEW REQUEST"
                table = "approval"
                dbas.insert_data(approval_data, table)
        except Exception as e:
            logger.error(f"Exception occurred: {e}")

##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    uvicorn.run("pras:app", host="localhost", port=5004, reload=True)