from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException,  Query, status, UploadFile, File, Form, APIRouter, Path
from fastapi.responses import JSONResponse, FileResponse
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
from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool
from sqlalchemy.orm import Session
from typing import Optional, List
from werkzeug.utils import secure_filename
import services.db_service as dbas
from services.db_service import get_session
from services.comment_service import add_comment
import pydantic_schemas as ps
from pydantic_schemas import CommentPayload, RequestPayload, ResponsePayload
import jwt  # PyJWT
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from docxtpl import DocxTemplate
from pathlib import Path

from services.auth_service import AuthService

from services.email_service import EmailService
from services.ldap_service import LDAPService, User
from services.search_service import SearchService
from services.uuid_service import uuid_service
from services.pdf_service import make_purchase_request_pdf
from services.request_management_service import RequestManagementService
from settings import settings

"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PRAS - (Purchase Request Approval System)
Will be used to keep track of purchase requests digitally through a central UI. This is the backend that will service
for the UI. When making a purchase request, user will use the their AD username for requestor.

TO LAUNCH SERVER:
uvicorn pras_api:app --port 5004
"""

# Load environment variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# ensure settings are loadeed and available
settings.PDF_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True, mode=0o750)

# Config variables
UPLOAD_FOLDER = os.path.join(os.getcwd(), os.getenv("UPLOAD_FOLDER", "uploads"))
PDF_OUTPUT_FOLDER = os.path.join(os.getcwd(), os.getenv("PDF_OUTPUT_FOLDER", "pdf_output"))
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

# Set the approvers emails
email_svc.set_first_approver("Roman Campbell", "roman_campbell@lawb.uscourts.gov")
email_svc.set_final_approver("Roman Campbell", "roman_campbell@lawb.uscourts.gov")

db_svc = next(get_session())  # Initialize with a session
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
##########################################################################
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
##########################################################################
@api_router.get("/getApprovalData", response_model=List[ps.ApprovalSchema])
async def get_approval_data(
    ID: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)):
    session = next(get_session())
    
    try:
        if ID:
            approval = dbas.get_approval_by_id(session, ID)
            if approval:
                approval_data = [ps.ApprovalSchema.model_validate(approval)]
            else:
                approval_data = []
        else:
            approvals = dbas.get_all_approval(session)
            approval_data = [ps.ApprovalSchema.model_validate(approval) for approval in approvals]
            logger.info(f"Approval data: {approval_data}")
        
        return approval_data
    finally:
        session.close()
        
##########################################################################
## GET STATEMENT OF NEED FORM
##########################################################################
@api_router.post("/downloadStatementOfNeedForm")
async def download_statement_of_need_form(
    payload: dict,
    current_user: User = Depends(get_current_user),
):
    ID = payload.get("ID")
    logger.debug(f"ID: {ID}")

    if not ID:
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    session = next(get_session())
    try:
        # Get all approvals with this ID
        approvals = session.query(dbas.Approval).filter(dbas.Approval.ID == ID).all()
        if not approvals:
            raise HTTPException(status_code=404, detail="No approvals found for this ID")
        
        # Convert to list of dicts
        rows = [ps.ApprovalSchema.model_validate(approval).model_dump() for approval in approvals]
        logger.debug(f"Approvals data: {rows}")
    
        # Build the PDF path
        pdf_path: Path = settings.PDF_OUTPUT_FOLDER / f"statement_of_need-{ID}.pdf"
        
        is_cyber = False
        
        # Generate PDF
        logger.info(f"ROWS: {rows}")
        make_purchase_request_pdf(rows=rows, output_path=pdf_path, is_cyber=is_cyber)
        
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Statement of need form not found")
        
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=pdf_path.name
        )
    finally:
        session.close()
    
##########################################################################
## GET SEARCH DATA
##########################################################################
@api_router.get("/getSearchData/search", response_model=List[ps.ApprovalSchema])
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
##########################################################################
@api_router.post("/sendToPurchaseReq")
async def set_purchase_request(data: dict, current_user: str = Depends(get_current_user)):
    logger.info(f"Authenticated user: {current_user}")
    if not data:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    logger.debug(f"DATA: {data}")
    
    requester = data.get("requester")
    items = data.get("items", [])
    
    if not requester:
        logger.error(f"Requester not found in ID: {data['ID']}")
        raise HTTPException(status_code=400, detail="Invalid requester")
    
    # Set the requester in the LDAP service
    ldap_svc.set_requester(requester)
    
    # Get requester email address
    requester_email = ldap_svc.get_email_address(ldap_svc.get_connection(), requester)
    if not requester_email: 
        logger.error(f"Could not find email for user {requester}")
        raise HTTPException(status_code=400, detail="Invalid requester")
    
    # Set the email service requester
    email_svc.set_requester(requester, requester_email)
    
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

    # Process each item in the items array
    items = data.get("items", [])
    if not items:
        logger.error("No items found in request data")
        raise HTTPException(status_code=400, detail="No items found in request data")
    
    # Get the shared ID from the first item, but ensure it's not a temporary ID
    first_item_id = items[0].get("ID") if items else None
    if not first_item_id or first_item_id.startswith("TEMP-"):
        shared_id = dbas.get_next_request_id()
        logger.info(f"Generated new shared ID: {shared_id}")
    else:
        shared_id = first_item_id
        logger.info(f"Using existing shared ID: {shared_id}")
        
    # Configure directory paths
    logger.info("Configuring email template");
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rendered_dir = os.path.join(project_root, "api", "rendered_templates")
    pdf_output_dir = os.path.join(project_root, "api", "pdf_output")
    template_path = os.path.join(project_root, "api", "templates", "son_template_lines.docx")
    
    email_svc.set_template_path(template_path)
    email_svc.set_rendered_dir(rendered_dir)
    
    is_cyber = False
    
    processed_lines = []
    # Process each item
    for item in items:
        item["ID"] = shared_id
        item["requester"] = requester
        
        # Process the purchase data
        processed_data = process_purchase_data(item)

        # Commit the purchase request
        purchase_req_commit(processed_data, current_user)
        processed_lines.append(processed_data)
    
    ##########################################################
    # CREATE EMAIL TEMPLATE HERE
    try:
        # Create PDF of purchase request for email
        os.makedirs(rendered_dir, exist_ok=True)
        
        pdf_filename = f"statement_of_need-{shared_id}.pdf"
        pdf_path = os.path.join(pdf_output_dir, pdf_filename)
        # Convert string path to Path object
        pdf_path_obj = Path(pdf_path)
        
        make_purchase_request_pdf(processed_lines, pdf_path_obj, is_cyber)
        logger.info(f"PDF generated at: {pdf_path}")
  
        # email_svc.set_rendered_docx_path(pdf_path)   # reuse same field
        # email_svc.send_notification(
        #     template_path=None,          # you can skip HTML template altogether
        #     template_data=None,
        #     subject="Your Purchase Order PDF",
        #     request_status="NEW REQUEST"
        # )
            
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {e}")
    
    return JSONResponse(content={"message": "Processing started in background"})
    
##########################################################################
## DELETE PURCHASE REQUEST table, condition, params
##########################################################################
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
##########################################################################
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
##########################################################################
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
## ASSIGN REQUISITION ID
##########################################################################
@api_router.post("/assignIRQ1_ID")
async def assign_IRQ1_ID(data: dict, current_user: User = Depends(get_current_user)):
    """
    This is called from the frontend to assign a requisition ID
    to the purchase request. It also updates the UUID in the approval table.
    IRQ number that is retrieved from JFIMS by Lela
    """
    logger.info(f"Assigning requisition ID: {data.get('IRQ1_ID')}")
    
    # Get the original ID from the request
    original_id = data.get('ID')
    if not original_id:
        raise HTTPException(status_code=400, detail="Missing ID in request")
    
    # Get the UUID using the UUID service
    with next(get_session()) as session:
        uuid = uuid_service.get_uuid_by_id(session, original_id)
    
    # update all tables with the new IRQ1_ID
    dbas.update_data_by_uuid(uuid=uuid, table="approvals", IRQ1_ID=data.get('IRQ1_ID'))
    dbas.update_data_by_uuid(uuid=uuid, table="line_item_statuses", IRQ1_ID=data.get('IRQ1_ID'))
    dbas.update_data_by_uuid(uuid=uuid, table="son_comments", IRQ1_ID=data.get('IRQ1_ID'))
    
    if not uuid:
        raise HTTPException(status_code=400, detail="Missing UUID in request")
    
    # Update the database with the requisition ID using the UUID
    dbas.update_data_by_uuid(uuid, "approvals", IRQ1_ID=data.get('IRQ1_ID'))
    return {"IRQ1_ID_ASSIGNED": True}

##########################################################################
## APPROVE/DENY PURCHASE REQUEST
# This endpoint will deal with all actions on a purchase request
##########################################################################
@api_router.post("/approveDenyRequest")
async def approve_deny_request(
    payload: RequestPayload,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Get amount of items and total price
    service = RequestManagementService(db)
    return service.approve_deny_request(
        request_id=payload.ID,
        uuid=payload.UUID,
        fund=payload.fund,
        action=payload.action,
        requester=current_user
    )

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
## CREATE NEW ID
##########################################################################
@api_router.post("/createNewID")
async def create_new_id(request: Request):
    """
    Create a new ID for a purchase request.
    """
    try:
        # Get the next request ID using the function from db_service
        new_id = dbas.get_next_request_id()
        logger.info(f"Created new ID: {new_id}")
        return {"ID": new_id}
    except Exception as e:
        logger.error(f"Error creating new ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
##########################################################################
## GET UUID BY ID
##########################################################################
@api_router.get("/getUUID/{ID}")
async def get_uuid_by_id_endpoint(ID: str, current_user: User = Depends(get_current_user)):
    """
    Get the UUID for a given ID.
    This endpoint can be used by other programs to retrieve the UUID.
    """
    logger.info(f"Getting UUID for ID: {ID}")
    
    with next(dbas.get_session()) as session:
        UUID = dbas.get_uuid_by_id(session, ID)
        
        if not UUID:
            raise HTTPException(status_code=404, detail=f"No UUID found for ID: {ID}")
            
        return {"UUID": UUID}
##########################################################################
## FETCH USERNAMES
##########################################################################
@api_router.get("/usernames", response_model=List[str])
async def get_usernames(q: str = Query(..., min_length=1, description="Prefix to search")):
    """
    Return a list of username strings that start with the given prefix `q`.
    """
    connection = ldap_svc.get_connection()
    if connection is None:
        logger.error("LDAP connection is None")
        return []
    logger.info(f"Fetching usernames for prefix: {q}")
    return ldap_svc.fetch_usernames(q)

##########################################################################
## POST COMMENT
##########################################################################
@api_router.post("/add_comment/{ID}")
async def add_comment_endpoint(
    payload: CommentPayload,
    ID: str = Path(description="The ID of the purchase request"),
):
    """
    Add a comment to an approval record.
    
    Args:
        ID: The ID of the approval record
        payload: The comment payload containing the comment text
        
    Returns:
        dict: Success message or error
    """
    logger.info(f"Received comment request for ID {ID} with payload: {payload}")
    current_date = datetime.now().strftime("%Y-%m-%d")
    formatted_comment = f"{current_date} - {payload.comment}"
    with next(get_session()) as session:
        success = add_comment(session, ID, payload.comment)
        if not success:
            raise HTTPException(status_code=404, detail="Failed to add comment")
        return {"message": "Comment added successfully"}
    
##########################################################################
## CYBER SECURITY RELATED
##########################################################################
@api_router.patch("/cyberSecRelated/{UUID}")
async def cyber_sec_related(UUID: str, isCyberSecRelated: bool):
    """
    Update the isCyberSecRelated field for a purchase request.
    """
    with next(get_session()) as session:
        success = dbas.update_data_by_uuid(session, UUID, isCyberSecRelated=isCyberSecRelated)
        return {"message": "Cybersec related field updated successfully"}

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
                # Handle the UUID field from the frontend
                if k == "UUID" and "UUID" in local_purchase_cols:
                    local_purchase_cols["UUID"] = v
                elif k in local_purchase_cols:
                    local_purchase_cols[k] = v
                
            nested_lnd = data.get('learnAndDev', {})
            train_not = bool(nested_lnd.get('trainNotAval', False))
            needs_not = bool(nested_lnd.get('needsNotMeet', False))
                
            # Build addComments field if trainNotAval or needsNotMeet is True
            if train_not or needs_not:
                comment = "Not available and/Or does not meet employee needs"
                existing = local_purchase_cols.get('addComments') or ""
                local_purchase_cols['addComments'] = (
                    existing + ("\n" if existing else "") + comment
                )
                # Add trainNotAval and needsNotMeet to local_purchase_cols
                local_purchase_cols['trainNotAval'] = train_not
                local_purchase_cols['needsNotMeet'] = needs_not
                
            if 'priceEach' in local_purchase_cols and 'quantity' in local_purchase_cols:
                try:
                    local_purchase_cols['priceEach'] = float(local_purchase_cols['priceEach'])
                    local_purchase_cols['quantity'] = int(local_purchase_cols['quantity'])
                    if local_purchase_cols['priceEach'] < 0 or local_purchase_cols['quantity'] <= 0:
                        raise ValueError("Invalid values")
                    local_purchase_cols['totalPrice'] = round(local_purchase_cols['priceEach'] * local_purchase_cols['quantity'], 2)
                    logger.success(f"TOTAL: {local_purchase_cols['totalPrice']}")
                    
                except ValueError as e:
                    logger.error("Invalid price or quantity:")
                    local_purchase_cols['totalPrice'] = 0
                    
        except Exception as e:
            logger.error(f"Error in process_purchase_data: {e}")
            
    return local_purchase_cols

##########################################################################
## PROCESS APPROVAL DATA --- send new request to approval
def process_approval_data(processed_data):
    logger.info(f"Processing approval data: {processed_data}")
    
    approval_data = {}
    
    if not isinstance(processed_data, dict):
        raise ValueError("Data must be a dictionary")
    
    logger.info(f"processed_data: {processed_data}")
    # Define allowed keys that correspond to the Approval model's columns.
    allowed_keys = [
        'UUID', 'purchase_request_uuid',
        'ID', 'requester', 'budgetObjCode', 'fund', 'trainNotAval', 'needsNotMeet',
        'itemDescription', 'justification', 'quantity', 'totalPrice', 'priceEach', 'location',
        'phoneext', 'datereq', 'dateneed', 'orderType'
]
    
    # Populate approval_data from processed_data
    for key, value in processed_data.items():
        # Handle the UUID field from the frontend
        if key == "UUID":
            approval_data["UUID"] = value
        elif key in allowed_keys:
            approval_data[key] = value
    
    # Set default values for required fields if not present
    # Handle IRQ1_ID - convert empty string to None to avoid unique constraint violation
    irq1_id = processed_data.get('IRQ1_ID', '')
    approval_data['IRQ1_ID'] = None if irq1_id == '' else irq1_id

    return approval_data

##########################################################################
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
def purchase_req_commit(processed_data, current_user: User):
    with lock:
        try:
            logger.info(f"Inserting purchase request data for ID: {processed_data['ID']}")
            
            # 1. First create purchase request
            purchase_request = dbas.insert_data(table="purchase_requests", data=processed_data)
            
            # 2. Process and create approval data
            approval_data = process_approval_data(processed_data)
            approval_data['status'] = dbas.ItemStatus.NEW
            approval_data['purchase_request_uuid'] = purchase_request.UUID
            approval = dbas.insert_data(table="approvals", data=approval_data)
            
            logger.info(f"Approval object: {approval}")
            logger.info(f"Approval UUID: {getattr(approval, 'UUID', None)}")
            
            # 3. Create line item status with required IDs and current user
            line_item_data = {
                'UUID': approval.UUID,
                'status': dbas.ItemStatus.NEW,
                'updated_by': current_user.username
            }
            line_item_status = dbas.insert_data(table="line_item_statuses", data=line_item_data)
            
            # 4. Create son comment with required IDs
            son_comment_data = {
                'UUID': approval.UUID,
                'purchase_request_id': processed_data['ID'],
                'son_requester': current_user.username
            }
            son_comment = dbas.insert_data(table="son_comments", data=son_comment_data)
            
            # Log the created objects
            logger.info(f"Created purchase request: {purchase_request}")
            logger.info(f"Created approval: {approval}")
            logger.info(f"Created line item status: {line_item_status}")
            logger.info(f"Created son comment: {son_comment}")
                
        except Exception as e:
            logger.error(f"Exception occurred: {e}")
            raise

##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    uvicorn.run("pras_api:app", host="localhost", port=5004, reload=True)