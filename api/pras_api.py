"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PRAS - (Purchase Request Approval System)
Will be used to keep track of purchase requests digitally through a central UI.
This is the backend that will service the UI. When making a purchase request, user will use their AD username for requestor.

TO LAUNCH SERVER:
uvicorn pras_api:app --port 5004
"""
from dataclasses import asdict
import sys
import os
import asyncio
import aiofiles
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uvicorn
import os, threading, time, uuid, json
import api.schemas.pydantic_schemas as ps

from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException,  Query, status, UploadFile, File, Form, APIRouter, Path
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from cachetools import TTLCache, cached
from typing import List, Optional
from loguru import logger
from dotenv import load_dotenv, find_dotenv
from sqlalchemy.orm import Session
from typing import Optional, List
from werkzeug.utils import secure_filename
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from pathlib import Path
from datetime import datetime

from api.services.db_service import get_session
from fastapi.security import OAuth2PasswordRequestForm
from api.services.auth_service import AuthService
from api.services.email_service.email_service import EmailService
from api.services.ldap_service import LDAPService
from api.services.search_service import SearchService
from api.services.uuid_service import uuid_service
from api.services.pdf_service import PDFService

from api.services.email_service.renderer import TemplateRenderer
from api.services.email_service.transport import OutlookTransport
from api.schemas.pydantic_schemas import EmailPayload, PurchaseItem, PurchaseRequestPayload
from api.services.email_service.email_service import EmailService

from api.settings import settings

from api.schemas.pydantic_schemas import PurchaseResponse
from api.schemas.pydantic_schemas import LDAPUser
from api.schemas.pydantic_schemas import CyberSecRelatedPayload
from api.schemas.pydantic_schemas import RequestPayload, GroupCommentPayload
from api.schemas.pydantic_schemas import ApprovalSchema

import api.services.db_service as dbas

# TODO: Investigate why rendering approval data is taking so long,
# TODO: There seems to be too much member validation in the approval schema when rendering the Approval Table

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

# Initialize auth service
auth_svc = AuthService(ldap_service=ldap_svc)
# OAuth2 scheme for JWT token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Initialize PDF service
pdf_svc = PDFService()

# Initialize search service
search_svc = SearchService()

# Initialize email service
renderer = TemplateRenderer(template_dir=str(settings.BASE_DIR / "services" / "email_service" / "templates"))
transport = OutlookTransport()
email_svc = EmailService(renderer=renderer, transport=transport, ldap_service=ldap_svc)

ldap_service = ldap_svc
db_svc = next(get_session())  # Initialize with a session

# Thread safety
lock = threading.Lock()

##########################################################################
# API router
api_router = APIRouter(prefix="/api", tags=["API Endpoints"])

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
    logger.info("""
        #####################################################################
        Login()
        #####################################################################""")
    
    return await auth_svc.login(form_data)
##########################################################################
## GET APPROVAL DATA
##########################################################################
@api_router.get("/getApprovalData", response_model=List[ApprovalSchema])
async def get_approval_data(
    ID: Optional[str] = Query(None),
    current_user: LDAPUser = Depends(auth_svc.get_current_user)):
    
    # Check if user is in IT group or CUE group
    logger.info(f"CURRENT USER: {current_user}")
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
    current_user: LDAPUser = Depends(auth_svc.get_current_user),
):
    """
    This endpoint is used to download the statement of need form for a given ID.
    """
    ID = payload.get("ID")
    if not ID:
        raise HTTPException(status_code=400, detail="ID is required")

    try:
        output_path = pdf_svc.create_pdf(
            ID=ID,
            payload=payload
        )
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Statement of need form not found")
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=output_path.name
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
##########################################################################
## GET SEARCH DATA
##########################################################################
@api_router.get("/getSearchData/search", response_model=List[ps.ApprovalSchema])
async def get_search_data(
    query: str = "",
    column: Optional[str] = None,
    current_user: LDAPUser = Depends(auth_svc.get_current_user)
):
    # If column is provided, use _exact_singleton_search instead
    if column:
        results = search_svc._exact_singleton_search(column, query, db=None)
    else:
        # Otherwise use the standard execute_search method
        results = search_svc.execute_search(query, db=None)
    
    return JSONResponse(content=jsonable_encoder(results))

##########################################################################
## COROUTINE FUNCTIONS
##########################################################################
# Save file async via aiofiles
async def _save_files(ID: str, file: UploadFile) -> str:
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    secure_name = secure_filename(file.filename)
    dest = os.path.join(settings.UPLOAD_FOLDER, f"{ID}_{secure_name}")
    
    # Read and write without blocking
    data = await file.read()
    async with aiofiles.open(dest, "wb") as out:
        await out.write(data)
        
    return dest

##########################################################################
# Send new request email on threads
async def _make_pdf_and_notify(payload: PurchaseRequestPayload, ID: str) -> str:
    try:
        # Make sure dir exists
        pdf_output_dir = settings.PDF_OUTPUT_FOLDER
        os.makedirs(pdf_output_dir, exist_ok=True)
        
        # Create PDF on thread
        pdf_path = await asyncio.to_thread(
            pdf_svc.create_pdf,
            ID=ID,
            payload=jsonable_encoder(payload)
        )
        
        # Convert to absolute path and verify it exists
        pdf_path = Path(pdf_path).resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        logger.info(f"PDF generated at: {pdf_path}")
        
        # Send new request email on thread
        await email_svc.send_new_request_to_requester(payload)
        await email_svc.send_new_request_to_approvers(payload, str(pdf_path))
        
        return str(pdf_path)
    except Exception as e:
        logger.error(f"Error in _make_pdf_and_notify: {e}")
        raise

##########################################################################
## SEND TO PURCHASE REQUEST -- being sent from the purchase req submit
##########################################################################
@api_router.post(
    "/sendToPurchaseReq",
    response_model=PurchaseResponse,
    status_code=200
)
async def set_purchase_request(
    payload_json: str = Form(..., description="JSON payload as string"),
    file: UploadFile = File(None),
    current_user: LDAPUser = Depends(auth_svc.get_current_user),
):
    try:
        payload = PurchaseRequestPayload.model_validate_json(payload_json)
    except Exception as e:
        logger.error(f"Error validating payload: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid payload format: {str(e)}")

    ################################################################3
    ## VALIDATE REQUESTER
    
    # Get requester from payload
    requester = payload.requester
    
    # Get requester email address
    requester_email = ldap_svc.get_email_address(ldap_svc.get_connection(), requester)
    
    if not requester_email: 
        logger.error(f"Could not find email for user {requester}")
        raise HTTPException(status_code=400, detail="Invalid requester")
    
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    ################################################################3
    ## VALIDATE/PROCESS PAYLOAD
    logger.debug(f"DATA: {payload}")
    
    requester = payload.requester
    items = payload.items
    
    # Process each item in the items array
    if not items:
        logger.error("No items found in request data")
        raise HTTPException(status_code=400, detail="No items found in request data")

    # Get the shared ID from the first item, but ensure it's not a temporary ID
    first_item_id = items[0].ID if items else None
    
    if not first_item_id or first_item_id.startswith("TEMP-"):
        shared_id = dbas.get_next_request_id()
        logger.info(f"Generated new shared ID: {shared_id}")
    else:
        shared_id = first_item_id
        logger.info(f"Using existing shared ID: {shared_id}")
        
    # Process each item
    for item in payload.items:
        item.ID = shared_id
        item.requester = payload.requester
        processed_data = process_purchase_data(item)
        purchase_req_commit(processed_data, current_user)
        
    # Build and launch asyncio tasks
    tasks: List[asyncio.Task] = []
    
    if file:
        tasks.append(asyncio.create_task(_save_files(shared_id, file)))
    
    # always gen pdf and send email
    tasks.append(asyncio.create_task(_make_pdf_and_notify(payload, shared_id)))
    
    # run concurently, wait for all to finish
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check for any exceptions
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Error in background task: {r}")
            raise HTTPException(status_code=500, detail=f"Error in background task: {r}")
    
    return JSONResponse({"message": "All work completed"})
        

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
async def assign_IRQ1_ID(data: dict, current_user: LDAPUser = Depends(auth_svc.get_current_user)):
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
    current_user: LDAPUser = Depends(auth_svc.get_current_user)
):
    try:
        logger.info(f"TARGET STATUS: {payload.target_status}")
        final_approvers = ["EdwardTakara", "EdmundBrown"]   # TESTING ONLY, prod use CUE groups
        
        # Before allowing the user to approve/deny, check if they are in the correct group
        # were looking for CUE group membership
        logger.info("Checking user group membership")
        user_group = ldap_svc.check_user_membership(ldap_svc.get_connection(), current_user.username)
        
        # Prepare and send email to approvers
        email_payload = EmailPayload(
            request_id=payload.request_id,
            requester_name=payload.requester_name,
            status=payload.status,
            message=payload.message,
            items=payload.items,
            link_to_request=settings.app_base_url,
        )
        logger.info(f"Constructed email payload: {email_payload}")
        email_svc.send_approval_email(email_payload)
        logger.success("SUCCESS!!!")
        logger.info(f"Payload: {payload}")
            
    except Exception as e:
        logger.error(f"Error approving/denying request: {e}")
        raise HTTPException(status_code=500, detail=f"Error approving/denying request: {e}")
    
    
    email_svc.send_approval_email(email_payload)
    
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
async def get_uuid_by_id_endpoint(ID: str, current_user: LDAPUser = Depends(auth_svc.get_current_user)):
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
            
            # Get requester's name from LDAP
            requester_info = ldap_svc.fetch_user(success.son_requester)
            requester_name = requester_info.username  # Using username as name since that's what we have
            logger.info(f"SUCCESS: {success}")
    # Send comment email
    email_svc.send_comment_email(payload, requster_email, requester_name)
    
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
def process_purchase_data(item: PurchaseItem) -> dict:
    with lock:
        local_purchase_cols = {col.name: None for col in dbas.PurchaseRequest.__table__.columns}
        try:
            for k, v in item.model_dump().items():
                if k in local_purchase_cols:
                    local_purchase_cols[k] = v
                
            nested_lnd = item.learnAndDev
            train_not = bool(nested_lnd.trainNotAval)
            needs_not = bool(nested_lnd.needsNotMeet)
                
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
##########################################################################
def purchase_req_commit(processed_data, current_user: LDAPUser):
    with lock:
        try:
            logger.info(f"Inserting purchase request data for ID: {processed_data['ID']}")
            
            if isinstance(processed_data.get('fileAttachments'), list):
                processed_data['fileAttachments'] = None
                
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
                'purchase_req_id': approval.ID,
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
## HANDLE FILE UPLOAD
##########################################################################
@api_router.post("/upload_file")
async def upload_file(ID: str = Form(...), file: UploadFile = File(...), current_user: LDAPUser = Depends(auth_svc.get_current_user)):
    # Ensure the upload directory exists
    if not os.path.exists(settings.UPLOAD_FOLDER):
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        
    try:
        secure_name = secure_filename(file.filename)
        new_filename = f"{ID}_{secure_name}"
        file_path = os.path.join(settings.UPLOAD_FOLDER, new_filename)
        logger.info(f"File path: {file_path}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"File saved: {file_path}")
        
        return JSONResponse(content={"message": "File uploaded successfully", "filename": new_filename})
    
    except Exception as e:
        logger.error(f"Error during file upload: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")
    
    
    
##########################################################################
## DELETE PURCHASE REQUEST table, condition, params
##########################################################################
async def delete_file(data: dict, current_user: LDAPUser = Depends(auth_svc.get_current_user)):
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
    files = os.listdir(settings.UPLOAD_FOLDER)
    file_found = False
    
    for file in files:
        if file == upload_filename:
            logger.info(f"Deleting file: {os.path.join(settings.UPLOAD_FOLDER, upload_filename)}")
            os.remove(os.path.join(settings.UPLOAD_FOLDER, file))
            file_found = True
            break

    if not file_found:
        raise HTTPException(status_code=404, detail="File not found")

    return {"delete": True}

##########################################################################
## MAIN CONTROL FLOW
##########################################################################
if __name__ == "__main__":
    uvicorn.run("pras_api:app", host="localhost", port=5004, reload=True)