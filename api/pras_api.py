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
from api.schemas.approval_schemas import ApprovalRequest, ApprovalSchema, DenyPayload
from api.schemas.purchase_schemas import AssignCOPayload
from api.services.approval_router.approval_handlers import ClerkAdminHandler
from api.services.approval_router.approval_router import ApprovalRouter
from api.schemas.comment_schemas import CommentItem
from pydantic import ValidationError
from fastapi import (FastAPI, APIRouter, Depends, Form, File, UploadFile, HTTPException, Request, Query, status)
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, text
from api.services.db_service import get_async_session
from api.schemas.enums import ItemStatus
import asyncio

# PRAS Miscellaneous Dependencies
from api.dependencies.misc_dependencies import *

# PRAS Dependencies
from api.dependencies.pras_dependencies import smtp_service
from api.dependencies.pras_dependencies import ldap_service
from api.dependencies.pras_dependencies import auth_service
from api.dependencies.pras_dependencies import pdf_service
from api.dependencies.pras_dependencies import search_service
from api.dependencies.pras_dependencies import settings
from api.schemas.email_schemas import LineItemsPayload, EmailPayloadRequest, EmailPayloadComment
from api.services.db_service import utc_now_truncated

# Database ORM Model Imports
from api.services.db_service import (
    PurchaseRequestHeader,
    PurchaseRequestLineItem,
    Approval,
    PendingApproval,
    SonComment,
    ContractingOfficer
)

# Schemas
from api.dependencies.pras_schemas import *
import api.services.db_service as dbas

# TODO: Investigate why rendering approval data is taking so long,
# TODO: There seems to be too much member validation in the approval schema when rendering the Approval Table
import tracemalloc
tracemalloc.start(10)

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
    token = await auth_service.create_access_token(user)
    
    # 3. Return token and user details
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": user.model_dump(),
    }
    
##########################################################################
## GET APPROVAL DATA
##########################################################################
@api_router.get("/getApprovalData", response_model=List[ApprovalSchema])
async def get_approval_data(
    ID: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    return await dbas.fetch_flat_approvals(db, ID=ID)
    
##########################################################################
## GET STATEMENT OF NEED FORM
##########################################################################
@api_router.post("/downloadStatementOfNeedForm")
async def download_statement_of_need_form(
    payload: dict,
    current_user: LDAPUser = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    This endpoint is used to download the statement of need form for a given ID.
    """
    ID = payload.get("ID")
    if not ID:
        raise HTTPException(status_code=400, detail="ID is required")

    try:
        output_path = await pdf_service.create_pdf(
            ID=ID,
            db=db,
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
@api_router.get("/getSearchData/search", response_model=List[ApprovalSchema])
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
async def _save_files(ID: str, file: UploadFile) -> str:
    try:
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        
        # Create secure filename
        secure_name = secure_filename(file.filename)
        dest = os.path.join(settings.UPLOAD_FOLDER, f"{ID}_{secure_name}")
        
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
    ID: str, 
    db: AsyncSession,
    uploaded_files: Optional[List[str]] = None) -> str:
    try:
        # Make sure dir exists
        pdf_output_dir = settings.PDF_OUTPUT_FOLDER
        os.makedirs(pdf_output_dir, exist_ok=True)
        
        # Use the asynchronous create_pdf method
        pdf_path = await pdf_service.create_pdf(
            ID=ID,
            db=db,
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
@api_router.post("/sendToPurchaseReq", response_model=PurchaseResponse)
async def send_purchase_request(
    payload_json: str = Form(..., description="JSON payload as string"),
    files: Optional[List[UploadFile]] = File(None, description="Multiple files"),
    current_user: LDAPUser = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    This endpoint:
      - Parses the incoming payload
      - Ensures the user is active via the LDAPUser we got from the token
      - Commits the request, tagging line items with current_user.username
    """
    try:
        payload: PurchaseRequestPayload = PurchaseRequestPayload.model_validate_json(payload_json)
        logger.info(f"Received files: {[f.filename for f in files] if files else 'No files'}")
        
    except ValidationError as e:
        error_details = e.errors()
        logger.error("PurchaseRequestPayload validation errors: %s", error_details)
        # Return them to the client so you know exactly what's wrong:
        return JSONResponse(
            status_code=422,
            content={
                "message": "Validation error",
                "errors": error_details
            }
        )

    logger.info("###########################################################")
    logger.info(f"CURRENT USER: {current_user}")
    logger.info("###########################################################")
    ################################################################3
    ## VALIDATE REQUESTER
    requester = payload.requester
    # Use current_user's email instead of doing another LDAP lookup
    requester_email = current_user.email
    
    if not requester_email: 
        logger.error(f"Could not find email for user {requester}")
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid requester"}
        )
    else:
        logger.info(f"Requester email: {requester_email}")
    
    if not payload:
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid data"}
        )
    
    #################################################################################
    ## BUILD EMAIL PAYLOADS
    #################################################################################
    items_for_email = [
        LineItemsPayload(
            budgetObjCode=item.budget_obj_code,
            itemDescription=item.item_description,
            location=item.location,
            justification=item.justification,
            quantity=item.quantity,
            priceEach=item.price_each,
            totalPrice=item.total_price,
            fund=item.fund
        )
        for item in payload.items
    ]
    logger.debug(f"THIS IS PAYLOAD: {payload}")
    # Build header & line items inside a single transaction
    pdf_path: str | None = None
    async with db.begin():
        # Generate the purchase request ID
        purchase_req_id = dbas.set_purchase_req_id()
        logger.debug(f"PURCHASE REQUEST ID: {purchase_req_id}")
        
        # PURCHASE REQUEST HEADER TABLE
        orm_pr_header = PurchaseRequestHeader(
            ID=purchase_req_id,
            IRQ1_ID=payload.irq1_id,
            CO=payload.co,
            requester=current_user.username,
            phoneext=payload.items[0].phoneext,
            datereq=payload.items[0].datereq,
            dateneed=payload.items[0].dateneed,
            orderType=payload.items[0].order_type,
        )
        db.add(orm_pr_header)
        await db.flush()  # makes ORM defaults (like pk/uuid) available
  
        pr_line_item_uuids: List[str] = []
        uploaded_files: List[str] = []
        
        # Handle case where no files are provided
        files_list = files or []
        
        for idx, item in enumerate(payload.items):
            file = files_list[idx] if idx < len(files_list) else None
            
            # Create line item
            orm_pr_line_item = PurchaseRequestLineItem(
                purchase_request_id=orm_pr_header.ID,
                itemDescription=item.item_description,
                justification=item.justification,
                addComments="; ".join(item.additional_comments) if item.additional_comments else None,
                trainNotAval=item.train_not_aval,
                needsNotMeet=item.needs_not_meet,
                budgetObjCode=item.budget_obj_code,
                fund=item.fund,
                quantity=item.quantity,
                priceEach=item.price_each,
                totalPrice=item.total_price,
                location=item.location,
                isCyberSecRelated=item.is_cyber_sec_related,
                status=item.status,
                created_time=utc_now_truncated(),
            )
            db.add(orm_pr_line_item)
            await db.flush() # UUID is now available
            
            # Save uploaded file if exists
            if file and file.filename:
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)
                
                filename = f"{orm_pr_line_item.UUID}_{file.filename}"
                full_path = upload_dir / filename
                
                with open(full_path, "wb") as f:
                    f.write(await file.read())
                    
                # Save file path to table in ORM model
                orm_pr_line_item.uploaded_file_path = str(full_path.resolve())
                uploaded_files.append(str(full_path.resolve()))
            
            # UUID tracking
            pr_line_item_uuids.append(orm_pr_line_item.UUID)
        
        

        # APPROVAL TABLE
        approvals: List[Approval] = []
        for item, line_uuid in zip(payload.items, pr_line_item_uuids):
            appr = Approval(
                UUID=str(uuid.uuid4()),
                purchase_request_id=orm_pr_header.ID,
                requester=payload.requester,
                phoneext=item.phoneext,
                datereq=item.datereq,
                dateneed=item.dateneed,
                orderType=item.order_type,
                itemDescription=item.item_description,
                justification=item.justification,
                trainNotAval=item.train_not_aval,
                needsNotMeet=item.needs_not_meet,
                budgetObjCode=item.budget_obj_code,
                fund=item.fund,
                priceEach=item.price_each,
                totalPrice=item.total_price,
                location=item.location,
                quantity=item.quantity,
                status=item.status,
                created_time=utc_now_truncated(),
            )
            db.add(appr)
            await db.flush()
            approvals.append(appr)
            
            if item.fund.startswith("511"):
                assigned_group = "IT"
            elif item.fund.startswith("092"):
                assigned_group = "FINANCE"

            task = PendingApproval(
                purchase_request_id=orm_pr_header.ID,
                line_item_uuid=line_uuid,
                approvals_uuid=appr.UUID,
                assigned_group=assigned_group,
                status=ItemStatus.NEW_REQUEST,
            )
            db.add(task)
            await db.flush()
            
            # Generate PDF once for the entire purchase request
            logger.info("Generating PDF document")
            pdf_path: str = await generate_pdf(payload, orm_pr_header.ID, db, uploaded_files)
            
            orm_pr_header.pdf_output_path = pdf_path
    # <--- transaction is committed here
    
    ################################################################3
    ## VALIDATE/PROCESS PAYLOAD
    logger.debug(f"DATA: {payload}")
    #fileAttachments=[FileAttachment(attachment=None, name='NBIS_questionaire_final.pdf', type='application/pdf', size=160428)])]
    
    requester = payload.requester
    items = payload.items
    
    # Process each item in the items array
    if not items:
        logger.error("No items found in request data")
        raise HTTPException(status_code=400, detail="No items found in request data")
    
    # Get ID from first item if not in payload
    if not payload.id and items:
        payload.id = items[0].id
    
    if not payload.id:
        logger.error("No ID found in request data")
        raise HTTPException(status_code=400, detail="ID is required")
    
    ##########################################################################
    ## EMAIL PAYLOADS
    ##########################################################################
    attachments_list = []
    
    if pdf_path is not None:
        attachments_list.append(pdf_path)
        
    for path in uploaded_files:
        if path is not None:
            attachments_list.append(path)
            
    # Build kwargs dict for Pydantic, omitting attachments until confirmed present
    payload_kwargs = {
        "model_type": "email_request",
        "ID": payload.id,
        "requester": payload.requester,
        "requester_email": requester_email,
        "datereq": payload.items[0].datereq,
        "dateneed": payload.items[0].dateneed,
        "orderType": payload.items[0].order_type,
        "subject": f"Purchase Request #{payload.id}",
        "sender": settings.smtp_email_addr,
        "to": None,
        "cc": None,
        "bcc": None,
        "text_body": None,
        "approval_link": settings.link_to_request,
        "items": items_for_email,
    }
    
    # Add attachments only if there are attachments to add
    if len(attachments_list) > 0:
        payload_kwargs["attachments"] = attachments_list
        
    # Now instatiate the email pydantic model
    email_request_payload = EmailPayloadRequest(**payload_kwargs)
    
    """
    # Make the to a condition, if this is a request from a requester, then we need to send it to the approvers
    # But we need to also send a confirmation to requester that is has been sent to the approvers
    """

    logger.info(f"EMAIL PAYLOAD REQUEST: {email_request_payload}")
    
    # Notify requester and approvers
    logger.info("Notifying requester and approvers")
    
    # Send request to approvers and requester
    async with asyncio.TaskGroup() as tg:
        tg.create_task(smtp_service.send_approver_email(email_request_payload, db=db))
        tg.create_task(smtp_service.send_requester_email(email_request_payload, db=db))
    
    return JSONResponse({"message": "All work completed"})

#########################################################################
## LOGGING FUNCTION - for middleware
#########################################################################
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
        try:
            # Get the response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Parse the response body
            error_payload = json.loads(response_body.decode("utf-8"))
            validation_errors = error_payload.get("errors", [])
            
            logger.error(
                {
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                    "raw_request_body": raw_json,
                    "validation_errors": validation_errors
                }
            )
            
            # Reconstruct the response
            return JSONResponse(
                status_code=422,
                content=error_payload,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            logger.error(f"Error parsing validation response: {e}")
            logger.error(
                {
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                    "raw_request_body": raw_json,
                    "validation_errors": "<unable to parse response body>"
                }
            )
            return response

    else:
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
async def assign_IRQ1_ID(
    data: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    This is called from the frontend to assign a requisition ID
    to the purchase request. It also updates the UUID in the approval table.
    IRQ number that is retrieved from JFIMS by Lela
    """
    logger.info(f"Assigning requisition ID: {data.get('IRQ1_ID')}")
    
    # Get the original ID from the request
    irq1_id = data.get('IRQ1_ID')
    original_id = data.get('ID')
    if not original_id or not irq1_id:
        raise HTTPException(status_code=400, detail="Missing ID in request")
    
    # Verify PurchaseRequestHeader exists
    stmt = select(PurchaseRequestHeader).where(PurchaseRequestHeader.ID == original_id)
    result = await db.execute(stmt)
    pr_header = result.scalar_one_or_none()
    
    if not pr_header:
        raise HTTPException(status_code=400, detail="PurchaseRequestHeader not found")
    
    # Update the IRQ1_ID
    await db.execute(
        update(PurchaseRequestHeader)
        .where(PurchaseRequestHeader.ID == original_id)
        .values(IRQ1_ID=irq1_id)
    )
    await db.commit()
    await db.refresh(pr_header)
    
    return {"IRQ1_ID_ASSIGNED": True}

#########################################################################
## ASSIGN CONTRACTING OFFICER
##########################################################################
@api_router.post("/assignCO")
async def assign_contracting_officer(
    payload: AssignCOPayload,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    try:
        row = await dbas.get_last_row_purchase_request_id(db=db)
        logger.info(f"ROW: {row}")
        if row.submission_status == "IN_PROGRESS":
            # Update the contracting officer
            stmt = (update(PurchaseRequestHeader)
                    .where(PurchaseRequestHeader.ID == row.ID)
                    .values(contracting_officer_id=payload.contracting_officer_id))
            await db.execute(stmt)
            await db.commit()
        logger.info(f"ASSIGN CO PAYLOAD: {payload}")
        
    except Exception as e:
        logger.error(f"Error assigning CO: {e}")
        raise HTTPException(status_code=500, detail=f"Error assigning CO: {e}")
    return {"message": "CO assigned successfully"}

#########################################################################
## DENY PURCHASE REQUEST
##########################################################################
@api_router.post("/denyRequest")
async def deny_request(
    payload: DenyPayload,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    logger.info(f"DENY PAYLOAD: {payload}")
    
    try:
        for ID, item_uuids, target_status, action in zip(
			payload.ID, payload.item_uuids, payload.target_status, payload.action
		):
            # Update the status to DENIED
            stmt = (update(
                PurchaseRequestLineItem)
                    .where(PurchaseRequestLineItem.UUID == item_uuids)
                    .values(status=target_status))
            await db.execute(stmt)
            await db.commit()
            
        # Process each item in the payload
        logger.info("REQUEST DENIED")
    except Exception as e:
        logger.error(f"Error denying request: {e}")
        raise HTTPException(status_code=500, detail=f"Error denying request: {e}")

##########################################################################
## APPROVE/DENY PURCHASE REQUEST
# This endpoint will deal with all actions on a purchase request
##########################################################################
@api_router.post("/approveRequest")
async def approve_deny_request(
    payload: RequestPayload,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    
    try:
        logger.info(f"PAYLOAD: {payload}")
        # Process each item in the payload
        results = []
        for i, (item_uuid, item_fund, total_price, target_status) in enumerate(zip(
            payload.UUID, payload.item_funds, payload.totalPrice, payload.target_status
        )):
            # Check if item is already in the chain
            stmt = select(PendingApproval.status).where(
                PendingApproval.line_item_uuid == item_uuid,
                PendingApproval.purchase_request_id == payload.ID
            )
            result = await db.execute(stmt)
            status_row = result.scalar_one_or_none()
            already_in_chain = status_row == ItemStatus.PENDING_APPROVAL
            
            # Decide which chain to use
            if already_in_chain:
                router = ApprovalRouter().start_handler(ClerkAdminHandler())
            else:
                router = ApprovalRouter() # Defaults to full chain: IT -> Finance -> ClerkAdmin
            #################################################################################################
            # START CHAIN
            # Get assigned group from pending_approvals via line_item_uuid/purchase_request_id
            stmt = select(
                PendingApproval.pending_approval_id,
                PendingApproval.assigned_group
            ).where(
                PendingApproval.line_item_uuid == item_uuid,
                PendingApproval.purchase_request_id == payload.ID
            )
            result = await db.execute(stmt)
            row = result.first()
            pending_approval_id = row.pending_approval_id
            assigned_group = row.assigned_group
            
            logger.info(f"Assigned group: {assigned_group}")
            logger.info(f"Pending approval ID: {pending_approval_id}")
            
            # Create approval request for the router
            approval_request = ApprovalRequest(
                id=payload.ID,
                uuid=item_uuid,
                pending_approval_id=pending_approval_id,
                fund=item_fund,
                assigned_group=assigned_group,
                status=target_status,
                total_price=total_price,
                action=payload.action,
                approver=current_user.username
            )
            result = await router.route(approval_request, db, current_user, ldap_service)
            logger.info(f"Result: {result}")
            #################################################################################################
            # END CHAIN
            #################################################################################################
            results.append({
                "uuid": item_uuid,
                "status": result.status.value if hasattr(result, 'status') else "processed",
                "action": payload.action
            })
        return results
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
            
        # Fetch user data from LDAP
        user = await ldap_service.fetch_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
            
        # Create new access token
        new_access_token = await auth_service.create_access_token(user)
        
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
@api_router.post("/createNewID")
async def create_new_id(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Create a new id for a purchase request.
        # insert into purchase request to start id creation, obtain the incremented id
        from purchase_request_seq_id, only allow the creation if the last row is submitted
    
    """
    try:
        # Start explicit transaction
        async with db.begin():
            # Grab explicit lock
            await db.execute(text("BEGIN EXCLUSIVE"))
            
            # Check last row status inside transaction
            last_row_status = await dbas.get_last_row_any_status(db=db)
            logger.info(f"Last row status: {last_row_status}")
            
            if last_row_status == "IN_PROGRESS":
                return {"ID": "PENDING"}
            
            if last_row_status == "SUBMITTED" or last_row_status is None:
                purchase_req_id = await dbas.set_purchase_req_id(db=db)
                logger.info(f"New purchase request id: {purchase_req_id}")
                return {"ID": purchase_req_id}
        
        raise HTTPException(status_code=400, detail="Could not create new ID due to race condition")
            
    except Exception as e:
        logger.error(f"Error creating new id: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
##########################################################################
## GET UUID BY ID
##########################################################################
@api_router.get("/getUUID/{ID}")
async def get_uuid_by_id_endpoint(
    ID: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Get the UUID for a given ID.
    This endpoint can be used by other programs to retrieve the UUID.
    """
    logger.info(f"Getting UUID for ID: {ID}")
    
    UUID = await dbas.get_uuid_by_id(db, ID)
    
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
    return await ldap_service.fetch_usernames(q)

##########################################################################
## ADD COMMENTS BULK
##########################################################################
@api_router.post("/add_comments")
async def add_comments(
    payload: GroupCommentPayload,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Add multiple comments to purchase requests.
    Args:
        payload: Contains list of comments with line_item UUIDs to update
    """
    logger.info(f"PAYLOAD: {payload}")
    
    updated_comments = []
    
    # Get approvals 
    for comment in payload.comment:
        logger.info(f"COMMENT: {comment}")
        
        # First, check if a SonComment already exists for this line_item_uuid
        existing_comment_stmt = select(SonComment).where(SonComment.line_item_uuid == comment.uuid)
        result = await db.execute(existing_comment_stmt)
        existing_comment = result.scalar_one_or_none()
        
        if existing_comment:
            # Update existing comment
            logger.info(f"Updating existing SonComment with UUID: {existing_comment.UUID}")
            stmt = (
                update(SonComment)
                .where(SonComment.UUID == existing_comment.UUID)
                .values(comment_text=comment.comment)
                .execution_options(synchronize_session="fetch")
            )
            await db.execute(stmt)
            updated_comments.append(existing_comment)
            
        else:
            # Create new SonComment record
            logger.info(f"Creating new SonComment for line_item_uuid: {comment.uuid}")
            
            # Get the line item to get additional info
            line_item_stmt = select(PurchaseRequestLineItem).where(PurchaseRequestLineItem.UUID == comment.uuid)
            result = await db.execute(line_item_stmt)
            line_item = result.scalar_one_or_none()
            
            logger.info(f"Line item: {line_item}")
            
            if not line_item:
                raise HTTPException(
                    status_code=404,
                    detail=f"PurchaseRequestLineItem with UUID {comment.uuid} not found"
                )
                
            # Get the approval uuid
            # Create new SonComment
            new_son_comment = SonComment(
                UUID=str(uuid.uuid4()),  # Generate new UUID for SonComment
                line_item_uuid=comment.uuid,
                comment_text=comment.comment,
                son_requester=current_user.username,
                item_description=line_item.itemDescription,
                created_at=utc_now_truncated()
            )
            
            db.add(new_son_comment)
            await db.flush()  # Get the generated UUID
            updated_comments.append(new_son_comment)
    
    # Commit all changes
    await db.commit()
    
    # Get requester info from the current user
    # Strip domain prefix if present (e.g., "ADU\romancampbell" -> "romancampbell")
    username_for_email = current_user.username
    if '\\' in username_for_email:
        username_for_email = username_for_email.split('\\')[-1]
    
    requester_email = await ldap_service.get_email_address(username_for_email)
    requester_name = current_user.username
    
    # Only send email if we can find the user's email address
    if requester_email:
        # Build email payload
        email_comments_payload = EmailPayloadComment(
            model_type      = "email_comments",
            ID              = payload.groupKey,           # reuse groupKey as the email ID
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
        
        # Send email notification
        await smtp_service.send_comments_email(payload=email_comments_payload, db=db)
        logger.info(f"Email notification sent to {requester_email}")
    else:
        logger.warning(f"Could not find email for user {username_for_email}, skipping email notification")

    return {"message": "Comments added successfully", "updated_count": len(updated_comments)}

##########################################################################
## CYBER SECURITY RELATED
##########################################################################
@api_router.put("/cyberSecRelated/{UUID}")
async def cyber_sec_related(
    UUID: str,
    payload: CyberSecRelatedPayload,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Update the isCyberSecRelated field for an Approval row.
    """
    # Fetch Approval row
    stmt = select(PurchaseRequestLineItem).where(PurchaseRequestLineItem.UUID == UUID)
    result = await db.execute(stmt)
    line_item = result.scalar_one_or_none()
    
    if line_item is None:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    # Apply only field that is being updated
    line_item.isCyberSecRelated = payload.isCyberSecRelated
    await db.commit()
    await db.refresh(line_item)
    
    return line_item

##########################################################################
## GET CONTRACTING OFFICER
##########################################################################
@api_router.get("/get_contracting_officer")
async def get_contracting_officer(
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Get a list of contracting officers.
    """
    stmt = select(ContractingOfficer)
    result = await db.execute(stmt)
    contracting_officers = result.scalars().all()
    
    return [
        {
            "id": co.id,
            "username": co.username,
            "email": co.email
        }
        for co in contracting_officers
    ]

##########################################################################
##########################################################################
## PROGRAM FUNCTIONS -- non API
##########################################################################
##########################################################################

# Register routes -- routes must be above this to be visible
app.include_router(api_router)
        
##########################################################################
## HANDLE FILE UPLOAD
##########################################################################
@api_router.post("/upload_file")
async def upload_file(ID: str = Form(...), file: UploadFile = File(...), current_user: LDAPUser = Depends(auth_service.get_current_user)):
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
async def delete_file(data: dict, current_user: LDAPUser = Depends(auth_service.get_current_user)):
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