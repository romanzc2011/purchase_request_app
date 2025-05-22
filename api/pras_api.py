"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PRAS - (Purchase Request Approval System)
Will be used to keep track of purchase requests digitally through a central UI.
This is the backend that will service the UI. When making a purchase request, user will use their AD username for requestor.

TO LAUNCH SERVER:
uvicorn pras_api:app --port 5004
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uvicorn
import jwt  # PyJWT
import os, threading, time, uuid, json
import api.schemas.pydantic_schemas as ps

from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException,  Query, status, UploadFile, File, Form, APIRouter, Path
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from cachetools import TTLCache, cached
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool
from sqlalchemy.orm import Session
from typing import Optional, List
from werkzeug.utils import secure_filename
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from docxtpl import DocxTemplate
from pathlib import Path
from pydantic import BaseModel


import api.services.db_service as dbas
from api.services.db_service import get_session
from fastapi.security import OAuth2PasswordRequestForm
from api.services.comment_service import add_comment
from api.services.auth_service import AuthService
from api.services.email_service.email_service import EmailService
from api.services.ldap_service import LDAPService, User
from api.services.search_service import SearchService
from api.services.uuid_service import uuid_service
from api.services.pdf_service import make_purchase_request_pdf
from api.schemas.pydantic_schemas import CyberSecRelatedPayload
from api.schemas.pydantic_schemas import RequestPayload, GroupCommentPayload
from api.schemas.pydantic_schemas import ApprovalSchema
from api.services.email_service.renderer import TemplateRenderer
from api.services.email_service.transport import OutlookTransport
from api.services.email_service.email_service import EmailService
from api.settings import settings

# Load environment variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# ensure settings are loadeed and available
settings.PDF_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True, mode=0o750)

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
# Instantiate your services with config from `settings`
ldap_svc = LDAPService(
    server_name=settings.ldap_server,
    port=settings.ldap_port,
    using_tls=settings.ldap_use_tls,
    service_user=settings.ldap_service_user,
    service_password=settings.ldap_service_password,
    it_group_dns=settings.it_group_dns,
    cue_group_dns=settings.cue_group_dns,
    access_group_dns=settings.access_group_dns
)
auth_svc = AuthService(ldap_service=ldap_svc)

# OAuth2 scheme for JWT token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

search_svc = SearchService()
renderer = TemplateRenderer(template_dir=os.path.join(os.getcwd(), "api", "services", "email_service", "templates"))
transport = OutlookTransport()
ldap_service = ldap_svc
db_svc = next(get_session())  # Initialize with a session
email_svc = EmailService(renderer=renderer, transport=transport, ldap_service=ldap_svc)

# Thread safety
lock = threading.Lock()



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


auth_svc = AuthService(ldap_service=ldap_svc)

##########################################################################
## LOGIN -- auth users and return JWTs
##########################################################################
@api_router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Expects:
      POST /api/login
      Content-Type: application/x-www-form-urlencoded

      username=...&password=...
    """
    user = auth_svc.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = auth_svc.create_access_token(user.username)
    return { "access_token": access_token, "token_type": "Bearer", "user": user.model_dump() }

##########################################################################
## GET APPROVAL DATA
##########################################################################
@api_router.get("/getApprovalData", response_model=List[ApprovalSchema])
async def get_approval_data(
    ID: Optional[str] = Query(None),
    current_user: User = Depends(auth_svc.get_current_user)):
    session = next(get_session())
    
    try:
        if ID:
            approval = dbas.get_approval_by_id(session, ID)
            if approval:
                approval_data = [ApprovalSchema.model_validate(approval)]
            else:
                approval_data = []
        else:
            approvals = dbas.get_all_approval(session)
            approval_data = [ApprovalSchema.model_validate(approval) for approval in approvals]
        
        return approval_data
    finally:
        session.close()
        
##########################################################################
## GET STATEMENT OF NEED FORM
##########################################################################
@api_router.post("/downloadStatementOfNeedForm")
async def download_statement_of_need_form(
    payload: dict,
    current_user: User = Depends(auth_svc.get_current_user),
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
        
        # Check if any line items are marked as cyber security related
        for row in rows:
            if row.get("isCyberSecRelated"):
                is_cyber = True
                break
        # Check if there are any comments in son_comments with this ID
        comment_arr = []
        with next(get_session()) as session:
            comments = session.query(dbas.SonComment).filter(dbas.SonComment.purchase_req_id == ID).all()
            if comments:
                for comment in comments:
                    comment_data = ps.SonCommentSchema.model_validate(comment)
                    comment_arr.append(comment_data.comment_text)
                    
        logger.info(f"Comment array: {comment_arr}")
                    
        make_purchase_request_pdf(rows=rows, output_path=pdf_path, is_cyber=is_cyber, comments=comment_arr)
        
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
    current_user: User = Depends(auth_svc.get_current_user)
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
async def set_purchase_request(data: dict, current_user: str = Depends(auth_svc.get_current_user)):
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
    pdf_output_dir = os.path.join(project_root, "api", "pdf_output")
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
        os.makedirs(pdf_output_dir, exist_ok=True)
        
        pdf_filename = f"statement_of_need-{shared_id}.pdf"
        pdf_path = os.path.join(pdf_output_dir, pdf_filename)
        # Convert string path to Path object
        pdf_path_obj = Path(pdf_path)
        
        make_purchase_request_pdf(processed_lines, pdf_path_obj, is_cyber)
        logger.info(f"PDF generated at: {pdf_path}")
  
        # Send email notification to REQUESTOR
        email_svc.send_template_email(
            to=[user_info.email],  # Use the email from user_info
            subject=f"Purchase Request Submitted - {shared_id}",
            template_name="request_submitted.html",
            context={
                "requester": requester,
                "request_id": shared_id,
                "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "items": processed_lines
            },
            attachments=[pdf_path]  # Attach the generated PDF
        )
        
        # Send email notification to APPROVERS
        email_svc.send_template_email(
            to=["roman_campbell@lawb.uscourts.gov"], # TESTING ONLY
            subject=f"Purchase Request Submitted - {shared_id}",
            template_name="request_submitted.html",
            context={
                "requester": requester,
                "request_id": shared_id,
                "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "items": processed_lines
            },
            attachments=[pdf_path]  # Attach the generated PDF
        )
            
    except Exception as e:
        logger.error(f"Error generating PDF or sending email: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {e}")
    
    return JSONResponse(content={"message": "Processing started in background"})
    
##########################################################################
## DELETE PURCHASE REQUEST table, condition, params
##########################################################################
@api_router.post("/deleteFile")
async def delete_file(data: dict, current_user: str = Depends(auth_svc.get_current_user)):
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
async def upload_file(ID: str = Form(...), file: UploadFile = File(...), current_user: str = Depends(auth_svc.get_current_user)):
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
async def assign_IRQ1_ID(data: dict, current_user: User = Depends(auth_svc.get_current_user)):
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
    current_user = Depends(auth_svc.get_current_user)
):
    logger.info(f"TARGET STATUS: {payload.target_status}")
    final_approvers = ["EdwardTakara", "EdmundBrown"]   # TESTING ONLY, prod use CUE groups
    # Before allowing the user to approve/deny, check if they are in the correct group
    # were looking for CUE group membership
    logger.info("Checking user group membership")
    user_group = ldap_svc.check_user_membership(ldap_svc.get_connection(), current_user.username)
    
    if not user_group["CUE_GROUP"]:
        logger.error(f"User {current_user.username} is not in the CUE group")
        raise HTTPException(status_code=403, detail="User not authorized to approve/deny requests")
    else:
        logger.info(f"User {current_user.username} is in the CUE group, continuing with approval process")
    
    logger.success("SUCCESS!!!")
    logger.info(f"Payload: {payload}")
    

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
async def get_uuid_by_id_endpoint(ID: str, current_user: User = Depends(auth_svc.get_current_user)):
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
## ADD COMMENTS BULK
##########################################################################
@api_router.post("/add_comments")
async def add_comments(payload: GroupCommentPayload):
    """
    Add multiple comments to purchase requests.

    Args:
        uuids: List of UUIDs of the purchase requests
        comments: List of comments to add
        
    Returns:
        dict: Success message or error
    """
    with next(get_session()) as session:
        # Get the number of elements in the comment list
        logger.info(f"PAYLOAD: {payload}")
        
        for comment in payload.comment:
            success = dbas.update_data_by_uuid(uuid=comment.uuid, table="son_comments", comment_text=comment.comment)
            if not success:
                raise HTTPException(status_code=404, detail="Failed to add comment")
            
            # Get requester and lookup email address
            requster_email = ldap_svc.get_email_address(ldap_svc.get_connection(), success.son_requester)
            logger.info(f"Requester email: {requster_email}")
            
            # Set the requester in email service
            email_svc.set_requester(success.son_requester, requster_email)
            
    # Send comment email
    email_svc.send_comment_email(payload)
    
    return {"message": "Comments added successfully"}

##########################################################################
## CYBER SECURITY RELATED
##########################################################################

@api_router.put("/cyberSecRelated/{UUID}")
async def cyber_sec_related(UUID: str, payload: CyberSecRelatedPayload):
    """
    Update the isCyberSecRelated field for a purchase request.
    """
    logger.info(f"Updating isCyberSecRelated for UUID: {UUID} to {payload.isCyberSecRelated}")
    with next(get_session()) as session:
        success = dbas.update_data_by_uuid(uuid=UUID, table="approvals", isCyberSecRelated=payload.isCyberSecRelated)
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
            
            # First create purchase request
            purchase_request = dbas.insert_data(table="purchase_requests", data=processed_data)
            
            # Process and create approval data
            approval_data = process_approval_data(processed_data)
            approval_data['status'] = dbas.ItemStatus.NEW
            approval_data['purchase_request_uuid'] = purchase_request.UUID
            approval = dbas.insert_data(table="approvals", data=approval_data)
            
            logger.info(f"Approval object: {approval}")
            logger.info(f"Approval UUID: {getattr(approval, 'UUID', None)}")
            
            # Create line item status with required IDs and current user
            line_item_data = {
                'UUID': approval.UUID,
                'status': dbas.ItemStatus.NEW,
                'updated_by': current_user.username
            }
            line_item_status = dbas.insert_data(table="line_item_statuses", data=line_item_data)
            
            # Create son comment with required IDs
            son_comment_data = {
                'UUID': approval.UUID,
                'purchase_req_id': approval.ID,  # <-- This is the correct key, matches your model
                'son_requester': current_user.username,
                'item_description': processed_data['itemDescription'],
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