"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PRAS - (Purchase Request Approval System)
Will be used to keep track of purchase requests digitally through a central UI.
This is the backend that will service the UI. When making a purchase request, user will use their AD username for requestor.

TO LAUNCH SERVER:
uvicorn pras_api:app --port 5004
"""

from datetime import datetime, timezone
import json
from api.schemas.comment_schemas import CommentItem
from api.schemas.purchase_schemas import PurchaseRequestLineItem
from pydantic import ValidationError
from fastapi import (
    FastAPI,
    APIRouter,
    Depends,
    BackgroundTasks,
    Form,
    File,
    UploadFile,
    HTTPException,
    Request,
    Query,
    status
)
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
# PRAS Miscellaneous Dependencies
from api.dependencies.misc_dependencies import *

# PRAS Dependencies
from api.dependencies.pras_dependencies import smtp_service
from api.dependencies.pras_dependencies import ldap_service
from api.dependencies.pras_dependencies import auth_service
from api.dependencies.pras_dependencies import pdf_service
from api.dependencies.pras_dependencies import search_service
from api.dependencies.pras_dependencies import uuid_service
from api.dependencies.pras_dependencies import settings
from api.services.cache_service import cache_service
from api.schemas.email_schemas import LineItemsPayload, EmailPayloadRequest, EmailPayloadComment

# Schemas
from api.dependencies.pras_schemas import *

# Singleton Services
from api.services.db_service import get_session, init_db

import api.services.db_service as dbas

# TODO: Investigate why rendering approval data is taking so long,
# TODO: There seems to be too much member validation in the approval schema when rendering the Approval Table
import tracemalloc
tracemalloc.start(10)

# Initialize FastAPI app
app = FastAPI(title="PRAS API")

# Initialize database
@app.on_event("startup")
def on_startup():
    init_db()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for JWT token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

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
    logger.info("☑️ Login()")
    
    # 1. Authenticate user and fetch LDAPUser
    user = await auth_service.authenticate_user(form_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Create JWT token
    token = auth_service.create_access_token(user)
    
    # 3. Return token and user details
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": user.model_dump(),
    }
    
##########################################################################
## GET APPROVAL DATA
##########################################################################
@api_router.get("/get_approval_data", response_model=List[ApprovalSchema])
async def get_approval_data(
    id: Optional[str] = Query(None),
    current_user: LDAPUser = Depends(auth_service.get_current_user)):
    
    # Check if user is in IT group or CUE group
    logger.info(f"CURRENT USER: {current_user}")
    with get_session() as session:
        try:
            if id:
                approval = dbas.get_approval_by_id(session, id)
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
@api_router.post("/download_statement_of_need_form")
async def download_statement_of_need_form(
    payload: dict,
    current_user: LDAPUser = Depends(auth_service.get_current_user),
):
    """
    This endpoint is used to download the statement of need form for a given id.
    """
    id = payload.get("id")
    if not id:
        raise HTTPException(status_code=400, detail="id is required")

    try:
        output_path = pdf_service.create_pdf(
            id=id,
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
@api_router.get("/get_search_data/search", response_model=List[ApprovalSchema])
async def get_search_data(
    query: str = "",
    column: Optional[str] = None,
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    # If column is provided, use _exact_singleton_search instead
    if column:
        results = search_service._exact_singleton_search(column, query, db=None)
    else:
        # Otherwise use the standard execute_search method
        results = search_service.execute_search(query, db=None)
    
    return JSONResponse(content=jsonable_encoder(results))

##########################################################################
## COROUTINE FUNCTIONS
##########################################################################
# Save file async via aiofiles
async def _save_files(id: str, file: UploadFile) -> str:
    try:
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        
        # Create secure filename
        secure_name = secure_filename(file.filename)
        dest = os.path.join(settings.UPLOAD_FOLDER, f"{id}_{secure_name}")
        
        logger.info("###########################################################")
        logger.info(f"Saving file to: {dest}")
        logger.info(f"filename: {file.filename}")
        logger.info("###########################################################")
        
        # Read and write without blocking
        data = await file.read()
        async with aiofiles.open(dest, "wb") as out:
            await out.write(data)
            
        logger.info(f"File saved successfully to: {dest}")
        return dest
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise

##########################################################################
# Generate PDF
async def generate_pdf(
    payload: PurchaseRequestPayload, 
    id: str, 
    uploaded_files: Optional[List[str]] = None) -> str:
    try:
        # Make sure dir exists
        pdf_output_dir = settings.PDF_OUTPUT_FOLDER
        os.makedirs(pdf_output_dir, exist_ok=True)
        
        # Create PDF on thread
        pdf_path = await asyncio.to_thread(
            pdf_service.create_pdf,
            id=id,
            payload=jsonable_encoder(payload)
        )
        
        # Convert to absolute path and verify it exists
        pdf_path = Path(pdf_path).resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        logger.info(f"PDF generated at: {pdf_path}")
        return str(pdf_path)
    except Exception as e:
        logger.error(f"Error in generate_pdf: {e}")
        raise

##########################################################################
## SEND TO PURCHASE REQUEST -- being sent from the purchase req submit
########################################################################## 
@api_router.post("/send_to_purchase_req", response_model=PurchaseResponse)
async def set_purchase_request(
    payload_json: str = Form(..., description="JSON payload as string"),
    files: Optional[List[UploadFile]] = File(None, description="Multiple files"),
    current_user: LDAPUser = Depends(auth_service.get_current_user),
):
    logger.info(f"Type of current_user: {type(current_user)}")

    """
    This endpoint:
      - Parses the incoming payload
      - Ensures the user is active via the LDAPUser we got from the token
      - Commits the request, tagging line items with current_user.username
    """
    try:
        logger.info(f"PAYLOAD JSON: {payload_json}")
        payload: PurchaseRequestPayload = PurchaseRequestPayload.model_validate_json(payload_json)
        logger.info(f"PAYLOAD: {payload}")
        logger.info(f"Received files: {[f.filename for f in files] if files else 'No files'}")
        
        # Build header data 
        request_data = payload.items[0]
        header_data = {
            "id":           request_data.id,
            "requester":    payload.requester,
            "phoneext":     request_data.phoneext,
            "datereq":      request_data.datereq,
            "dateneed":     request_data.dateneed,
            "order_type":   request_data.order_type,
            "status":       request_data.status,
            "created_time": datetime.now(timezone.utc),
        }
        logger.info(f"HEADER DATA: {header_data}")
        # Insert header data into purchase request tabl
        
        # Loop through the line items and extract line item data of purchase_request
        for item in payload.items:
            line_data = {
                "purchase_request_uuid":    hdr.uuid,
                "item_description":         item.item_description,
                "justification":            item.justification,
                "add_comments":             item.add_comments,
                "train_not_aval":           item.train_not_aval,
                "needs_not_meet":           item.needs_not_meet,
                "budget_obj_code":          item.budget_obj_code,
                "fund":                     item.fund,
                "quantity":                 item.quantity,
                "price_each":               item.price_each,
                "total_price":              item.total_price,
                "location":                 item.location,
                "is_cyber_sec_related":     item.is_cyber_sec_related,
                "status":                   item.status,
                "created_time":             datetime.now(timezone.utc),
            }
            
            logger.info(f"LINE DATA: {line_data}")
            hdr = dbas.insert_data("purchase_requests", header_data)
            line_item = dbas.insert_data("line_items", line_data)
            
            exit(0)
        
    except ValidationError as e:
        logger.error("PurchaseRequestPayload errors: %s", e.errors())
        # Return them to the client so you know exactly what's wrong:
        raise HTTPException(status_code=422, detail=e.errors())

    ################################################################3
    ## VALidATE REQUESTER
    requester = payload.requester
    requester_email = await ldap_service.get_email_address(requester)
    
    if not requester_email: 
        logger.error(f"Could not find email for user {requester}")
        raise HTTPException(status_code=400, detail="Invalid requester")
    
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    ################################################################3
    ## VALidATE/PROCESS PAYLOAD
    logger.debug(f"DATA: {payload}")
    #fileAttachments=[FileAttachment(attachment=None, name='NBIS_questionaire_final.pdf', type='application/pdf', size=160428)])]
    
    requester = payload.requester
    items = payload.items
    
    # Process each item in the items array
    if not items:
        logger.error("No items found in request data")
        raise HTTPException(status_code=400, detail="No items found in request data")

    # Get the shared id from the first item, but ensure it's not a temporary id
    first_item_id = items[0].id if items else None
    
    # Generate a new shared id if the first item id is not a temporary id - this keeps the LAWB id unique just incrementing
    if not first_item_id:
        shared_id = dbas.get_next_request_id()
        logger.info(f"Generated new shared id: {shared_id}")
    else:
        shared_id = first_item_id
        logger.info(f"Using existing shared id: {shared_id}")
        
    # Process each item
    for item in payload.items:
        logger.info(f"Before assigning shared id: {item.id}")
        item.id = shared_id
        logger.info(f"After assigning shared id: {item.id}")
        
        item.requester = payload.requester
        processed_data = process_purchase_data(item)
        purchase_req_commit(processed_data, current_user)
    
    # Update the payload with the shared id
    payload.id = shared_id  
    
    # Create tasks list for files
    uploaded_files = []
    if files:
        for file in files:
            logger.info(f"Saving uploaded file: {file.filename}")
            uploaded_files.append(await _save_files(shared_id, file))
    
    # Generate PDF
    logger.info("Generating PDF document")
    pdf_path: str = await generate_pdf(payload, shared_id, uploaded_files)
    #################################################################################
    ## BUILD EMAIL PAYLOADS
    #################################################################################
    add_comments = cache_service.get_or_set(
        "comments",
        payload.id,
        lambda: dbas.get_additional_comments_by_id(payload.id)
    )
    
    for item in payload.items:
        item.add_comments = add_comments
    
    items_for_email = [
        LineItemsPayload(**item.model_dump())
        for item in payload.items
    ]
    
    #################################################################################
    ## EMAIL PAYLOADS
    #################################################################################
    email_request_payload = EmailPayloadRequest(
        model_type="email_request",
        id=payload.id,
        requester=payload.requester,
        requester_email=requester_email,
        datereq=payload.items[0].datereq,
        dateneed=payload.items[0].dateneed,
        order_type=payload.items[0].order_type,
        subject=f"Purchase Request #{payload.id}",
        sender=settings.smtp_email_addr,
        to=None,   # Assign this in the smtp service
        cc=None,
        bcc=None,
        text_body=None,
        approval_link=f"{settings.link_to_request}",
        items=items_for_email,
        attachments=[pdf_path, *uploaded_files]
    )
    
    """
    # Make the to a condition, if this is a request from a requester, then we need to send it to the approvers
    # But we need to also send a confirmation to requester that is has been sent to the approvers
    """

    logger.info(f"EMAIL PAYLOAD REQUEST: {email_request_payload}")
    
    # Notify requester and approvers
    logger.info("Notifying requester and approvers")
    
    # Send request to approvers and requester
    async with asyncio.TaskGroup() as tg:
        tg.create_task(smtp_service.send_approver_email(email_request_payload))
        tg.create_task(smtp_service.send_requester_email(email_request_payload))
    
    return JSONResponse({"message": "All work completed"})

#########################################################################
## LOGGING FUNCTION - for middleware
##########################################################################
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Capture raw body text
    body_bytes = await request.body()
    try:
        raw_json = body_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raw_json = "<could not decode body>"
        
    # We need to replace request._receive so that downstream code still sees the body
    async def receive_override():
        return {"type": "http.request", "body": body_bytes}

    request._receive = receive_override  # overwrite the receive coroutine

    # --- Call the next handler and get the response ---
    response = await call_next(request)
    elapsed = time.time() - start_time

    # --- If it's a validation error (422), log the body and the validation details ---
    if response.status_code == 422:
        # JSONResponse stores its content in .body
        # For a 422 FastAPI Response, .body is a JSON‐encoded byte string of { "detail": […] }
        try:
            error_payload = json.loads(response.body.decode("utf-8"))
        except Exception:
            error_payload = {"raw_response": "<unable to parse response body>"}

        logger.error(
            {
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "elapsed": elapsed,
                "raw_request_body": raw_json,
                "validation_errors": error_payload.get("detail", error_payload),
            }
        )

    else:
        logger.bind(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            elapsed=elapsed,
        ).info("Request processed")

    response.headers["X-Request-id"] = request_id
    return response

#########################################################################
## ASSIGN REQUISITION id
##########################################################################
@api_router.post("/assignirq1_id")
async def assign_irq1_id(data: dict, current_user: LDAPUser = Depends(auth_service.get_current_user)):
    """
    This is called from the frontend to assign a requisition id
    to the purchase request. It also updates the uuid in the approval table.
    IRQ number that is retrieved from JFIMS by Lela
    """
    logger.info(f"Assigning requisition id: {data.get('irq1_id')}")
    
    # Get the original id from the request
    original_id = data.get('id')
    if not original_id:
        raise HTTPException(status_code=400, detail="Missing id in request")
    
    # Get the uuid using the uuid service
    with get_session() as session:
        uuid = uuid_service.get_uuid_by_id(session, original_id)
    
    # update all tables with the new irq1_id
    dbas.update_data_by_uuid(uuid=uuid, table="approvals", irq1_id=data.get('irq1_id'))
    dbas.update_data_by_uuid(uuid=uuid, table="line_item_statuses", irq1_id=data.get('irq1_id'))
    dbas.update_data_by_uuid(uuid=uuid, table="son_comments", irq1_id=data.get('irq1_id'))
    
    if not uuid:
        raise HTTPException(status_code=400, detail="Missing uuid in request")
    
    # Update the database with the requisition id using the uuid
    dbas.update_data_by_uuid(uuid, "approvals", irq1_id=data.get('irq1_id'))
    return {"irq1_id_ASSIGNED": True}

##########################################################################
## APPROVE/DENY PURCHASE REQUEST
# This endpoint will deal with all actions on a purchase request
#final_approvers = ["EdwardTakara", "EdmundBrown"]   # TESTING ONLY, prod use CUE groups

##########################################################################

@api_router.post("/approve_deny_request")
async def approve_deny_request(
    payload: RequestPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    try:
        # Get size of payload and filter data
        payload_count = payload.item_count
        payload_data = payload.model_dump()
        logger.info(f"PAYLOAD DATA: {payload_data}")
            
        logger.info(f"INCOMING PAYLOAD: {payload}")
    except Exception as e:
        logger.error(f"Error approving/denying request: {e}")
        raise HTTPException(status_code=500, detail=f"Error approving/denying request: {e}")
    
##########################################################################
## REFRESH TOKEN
@api_router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        # Verify the refresh token
        username = auth_service.verify_jwt_token(refresh_token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
        # Create new access token
        new_access_token = auth_service.create_access_token(identity=username)
        
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
## CREATE NEW id
##########################################################################
@api_router.post("/create_new_id")
async def create_new_id(request: Request):
    """
    Create a new id for a purchase request.
    """
    try:
        purchase_req_id = dbas.set_purchase_req_id()
        logger.info(f"New purchase request id: {purchase_req_id}")
        return {"id": purchase_req_id}
    except Exception as e:
        logger.error(f"Error creating new id: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
##########################################################################
## GET uuid BY id
##########################################################################
@api_router.get("/get_uuid/{id}")
async def get_uuid_by_id_endpoint(id: str, current_user: LDAPUser = Depends(auth_service.get_current_user)):
    """
    Get the uuid for a given id.
    This endpoint can be used by other programs to retrieve the uuid.
    """
    logger.info(f"Getting uuid for id: {id}")
    
    with get_session() as session:
        uuid = dbas.get_uuid_by_id(session, id)
        
        if not uuid:
            raise HTTPException(status_code=404, detail=f"No uuid found for id: {id}")
            
        return {"uuid": uuid}
##########################################################################
## FETCH USERNAMES
##########################################################################
@api_router.get("/usernames", response_model=List[str])
async def get_usernames(q: str = Query(..., min_length=1, description="Prefix to search")):
    """
    Return a list of username strings that start with the given prefix `q`.
    """
    return await ldap_service.fetch_usernames(q)

##########################################################################
## ADD COMMENTS BULK
##########################################################################
@api_router.post("/add_comments")
async def add_comments(payload: GroupCommentPayload):
    """
    Add multiple comments to purchase requests.

    Args:
        uuids: List of uuids of the purchase requests
        comments: List of comments to add
    """
    with get_session() as session:
        # Get the number of elements in the comment list
        logger.info(f"PAYLOAD: {payload}")
        
        for comment in payload.comment:
            logger.info(f"COMMENT: {comment}")
            success = dbas.update_data_by_uuid(uuid=comment.uuid, table="son_comments", comment_text=comment.comment)
            if not success:
                raise HTTPException(status_code=404, detail="Failed to add comment")
            
            # Get requester and lookup email address
            requester_email = await ldap_service.get_email_address(success.son_requester)
            requester_info = await ldap_service.fetch_user(success.son_requester)
            requester_name = requester_info.username

        # Build email payload
        email_comments_payload = EmailPayloadComment(
            model_type      = "email_comments",
            id              = payload.groupKey,           # reuse groupKey as the email id
            requester       = requester_name,
            requester_email = requester_email,
            datereq         = datetime.now().date(),
            subject         = f"Purchase Request #{payload.groupKey} – New Comments",
            sender          = settings.smtp_email_addr,
            to              = None, 
            cc              = None,
            bcc             = None,
            text_body       = None,
            comment_data    = [payload], 
        )
        
        # Get data about the request from Approvals table
        await smtp_service.send_comments_email(payload=email_comments_payload)

    
    return {"message": "Comments added successfully"}

##########################################################################
## CYBER SECURITY RELATED
##########################################################################
@api_router.put("/cyber_sec_related/{uuid}")
async def cyber_sec_related(uuid: str, payload: CyberSecRelatedPayload):
    """
    Update the isCyberSecRelated field for a purchase request.
    """
    logger.info(f"Updating isCyberSecRelated for uuid: {uuid} to {payload.isCyberSecRelated}")
    with get_session() as session:
        success = dbas.update_data_by_uuid(uuid=uuid, table="approvals", isCyberSecRelated=payload.isCyberSecRelated)
        return {"message": "Cybersec related field updated successfully"}

##########################################################################
##########################################################################
## PROGRAM FUNCTIONS -- non API
##########################################################################
##########################################################################

app.include_router(api_router)

##########################################################################
## PROCESS PURCHASE DATA
def process_purchase_data(item: PurchaseRequestLineItem) -> dict:
    with lock:
        local_purchase_cols = {
            col.name: None
            for col in dbas.PurchaseRequest.__table__.columns
        }
        
        try:
            for k, v in item.model_dump().items():
                if k in local_purchase_cols:
                    local_purchase_cols[k] = v
                    logger.info(f"LOCAL PURCHASE COLS: {k} = {v}")
                    
            # Handle comments based on trainNotAval and needsNotMeet
            comments_list = []
            
            if local_purchase_cols['train_not_aval'] == True:
                comments_list.append("Training not available")
                
            if local_purchase_cols['needs_not_meet'] == True:
                comments_list.append("Does not meet employee needs")
                
            if comments_list:
                local_purchase_cols['addComments'] = ";".join(comments_list)
            else: 
                local_purchase_cols['addComments'] = None
                
            # Recalculate total price
            price_each = local_purchase_cols['price_each']
            quantity = local_purchase_cols['quantity']
            
            if price_each is not None and quantity is not None:
                try:
                    price_each = float(price_each)
                    quantity = int(quantity)
                    
                    if price_each < 0 or quantity <= 0:
                        raise ValueError("Invalid values")
                    
                    local_purchase_cols['total_price'] = round(price_each * quantity, 2)
                    
                except ValueError as e:
                    logger.error(f"Invalid price or quantity: {e}")
                    local_purchase_cols['total_price'] = 0
                    
        except Exception as e:
            logger.error(f"Error in process_purchase_data: {e}")
            raise
       
            
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
        'uuid', 'purchase_request_uuid',
        'id', 'requester', 'budget_obj_code', 'fund', 'train_not_aval', 'needs_not_meet',
        'item_description', 'justification', 'quantity', 'total_price', 'price_each', 'location',
        'phoneext', 'datereq', 'dateneed', 'order_type'
]
    
    # Populate approval_data from processed_data
    for key, value in processed_data.items():
        # Handle the uuid field from the frontend
        if key == "uuid":
            approval_data["uuid"] = value
        elif key in allowed_keys:
            approval_data[key] = value
    
    # Set default values for required fields if not present
    # Handle irq1_id - convert empty string to None to avoid unique constraint violation
    irq1_id = processed_data.get('irq1_id', '')
    approval_data['irq1_id'] = None if irq1_id == '' else irq1_id

    return approval_data

##########################################################################
## BACKGROUND PROCESS FOR PROCESSING PURCHASE REQ DATA
##########################################################################
def purchase_req_commit(processed_data: dict, current_user: LDAPUser):
    with lock:
        try:
            logger.info(f"Inserting purchase request data for id: {processed_data['id']}")
            
            if isinstance(processed_data.get('file_attachments'), list):
                processed_data['file_attachments'] = None
                
            # First create purchase request
            purchase_request = dbas.insert_data(table="purchase_requests", data=processed_data)
            
            # Process and create approval data
            approval_data = process_approval_data(processed_data)
            approval_data['status'] = dbas.ItemStatus.NEW
            approval_data['purchase_request_uuid'] = purchase_request.uuid
            approval = dbas.insert_data(table="approvals", data=approval_data)
            
            logger.info(f"Approval object: {approval}")
            logger.info(f"Approval uuid: {getattr(approval, 'uuid', None)}")
            
            # Create line item status with required ids and current user
            line_item_data = {
                'uuid': approval.uuid,
                'status': dbas.ItemStatus.NEW,
                'updated_by': current_user.username
            }
            line_item_status = dbas.insert_data(table="line_item_statuses", data=line_item_data)
            
            # Create son comment with required ids
            son_comment_data = {
                'uuid': approval.uuid,
                'purchase_req_id': approval.id,
                'son_requester': current_user.username,
                'item_description': processed_data['item_description'],
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
async def upload_file(id: str = Form(...), file: UploadFile = File(...), current_user: LDAPUser = Depends(auth_service.get_current_user)):
    # Ensure the upload directory exists
    if not os.path.exists(settings.UPLOAD_FOLDER):
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        
    try:
        secure_name = secure_filename(file.filename)
        new_filename = f"{id}_{secure_name}"
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
async def delete_file(data: dict, current_user: LDAPUser = Depends(auth_service.get_current_user)):
    """
    Deletes a file given its id and filename.
    Expects a JSON payload containing "id" and "filename".
    """
    if not data:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    id = data.get("id")
    filename = data.get("filename")
    if not id or not filename:
        raise HTTPException(status_code=400, detail="Missing id or filename")
    
    # Construct the upload filename
    upload_filename = f"{id}_{filename}"
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