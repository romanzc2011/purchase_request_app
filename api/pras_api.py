"""
AUTHOR: Roman Campbell
DATE: 01/03/2025
NAME: PRAS - (Purchase Request Approval System)
Will be used to keep track of purchase requests digitally through a central UI.
This is the backend that will service the UI. When making a purchase request, user will use their AD username for requestor.

EXPLANATION OF THE pending_approvals and final_approvals TABLES: The pending_approvals is to show the process the current
	status of their ItemStatus.status for future decisions. The final_approvals are used during the actual approval process,
	the users do not interact with final_approvals, it more of a metadata table
 
EXPLANATION OF COMMENT COLORS:
	# ! Progress tracking (RED)
	# * (GREEN)
	# ? (BLUE)
	# // General note (GRAY)
	# TODO:
 
 # TODO: To remove socketio logging go to Line 10 of sio_instance.py and set logger and engineio_logger to False

TO LAUNCH SERVER:
uvicorn pras_api:app --host 127.0.0.1 --port 5004
"""
from datetime import datetime
import json
import time
import signal
import socketio
from pathlib import Path
from typing import Awaitable, Callable, ParamSpec, TypeVar
from api.schemas.approval_schemas import ApprovalRequest, ApprovalSchema, DenyPayload, UpdatePricesPayload, UpdateBocLocFundPayload, BocLocFundPayload
from api.schemas.boc_fund_mapping.boc_to_fund_mapping import BocMapping092000, BocMapping51140X, BocMapping51140E
from api.schemas.purchase_schemas import AssignCOPayload
from api.services.approval_router.approval_handlers import ClerkAdminHandler
from api.services.approval_router.approval_router import ApprovalRouter
from api.services.progress_tracker.steps.download_steps import DownloadStepName
from api.services.progress_tracker.steps.submit_request_steps import SubmitRequestStepName
from api.utils.misc_utils import format_username, reset_signals, error_handler
from pydantic import ValidationError
from fastapi import (
    FastAPI, APIRouter, Depends, Form, 
    File, UploadFile, HTTPException, Request, 
    Query, status, WebSocket, WebSocketDisconnect)
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from api.utils.logging_utils import logger_init_ok

# SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, text, func, exists, insert 
from api.services.db_service import get_async_session
from api.schemas.enums import AssignedGroup, CueClerk, ItemStatus, LDAPGroup
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
from api.services.progress_tracker.progress_manager import create_approval_tracker, create_download_tracker, create_submit_request_tracker, get_submit_request_tracker
from api.services.progress_tracker.steps.approval_steps import ApprovalStepName
from api.services.socketio_server.sio_instance import sio
from api.services.socketio_server.sio_events import sio
import api.services.socketio_server.sio_events as sio_events
from api.services.ipc_status import ipc_status
import time

# Database ORM Model Imports
from api.services.db_service import (
    PurchaseRequestHeader,
    PurchaseRequestLineItem,
    Approval,
    PendingApproval,
    SonComment,
    ContractingOfficer,
    BudgetObjCode,
    BudgetFund
)
# Schemas
from api.dependencies.pras_schemas import *

import api.services.db_service as dbas
import tracemalloc
tracemalloc.start(10)

# Set up signal handlers
signal.signal(signal.SIGTERM, error_handler)
signal.signal(signal.SIGINT, error_handler)

# Initialize FastAPI app
app = FastAPI(title="PRAS API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://10.222.49.26:5002", "http://localhost:5002", "http://127.0.0.1:5002", "https://10.234.198.113:5002", "https://LAWB-SHCOL-7920.adu.dcn:5002"],  # Your frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

api_router = APIRouter(prefix="/api", tags=["API Endpoints"])

# Create socketio server
app.mount("/progress_bar_bridge", socketio.ASGIApp(sio, app, socketio_path="communicate"))

# OAuth2 scheme for JWT token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Thread safety
lock = threading.Lock()

# Set generic return type/ arg types
P = ParamSpec("P")
R = TypeVar("R")
    
@app.on_event("startup")
async def initialize_database():
    """Initialize the database on startup"""
    from api.services.db_service import init_db
    try:
        await init_db()
        logger_init_ok("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e

@app.on_event("startup")
async def initialize_search_service():
    """Initialize the search service after database is ready"""
    from api.dependencies.pras_dependencies import get_search_service
    try:
        # This will create the search service and build the index
        get_search_service()
        logger_init_ok("Search service initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing search service: {e}")
        # Don't raise here as search service is not critical for startup

@app.on_event("startup")
async def _capture_loop():
    from api.services.socketio_server.sio_instance import set_server_loop
    try:
        set_server_loop(asyncio.get_event_loop())
    except Exception as e:
        logger.error(f"Error setting server loop: {e}")
        logger_init_ok("Server loop failed to set")
        raise e
    
# Start LDAP heartbeat to prevent connection timeout
@app.on_event("startup")
async def start_keepalive_ldap():
    logger_init_ok("LDAP keepalive starting")
    # Start the keepalive task in the background
    try:
        asyncio.create_task(ldap_service.start_keepalive_ldap())
    except Exception as e:
        logger.error(f"Error starting LDAP keepalive: {e}")
        logger_init_ok("LDAP keepalive failed to start")
        raise e
    
@app.on_event("startup")
async def _install_loop_exception_handler():
    loop = asyncio.get_running_loop()
    logger_init_ok("Installing loop exception handler")
    def handler(loop, context):
        exc = context.get("exception")
        if isinstance(exc, asyncio.CancelledError):
            logger.debug("Loop exception handler: CancelledError")
            return
        loop.default_exception_handler(context)
    loop.set_exception_handler(handler)
    
@app.on_event("startup")
async def setup_logging():
    logger.add("logs/error.log", level="ERROR", rotation="10 MB", retention="10 days")
    logger_init_ok("Logging setup complete")
    
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
    try:
        user = await auth_service.authenticate_user(form_data)
        
        # Check if user is a string (invalid credentials) or None
        if isinstance(user, str) or user is None:
            logger.info(f"INVALID CREDENTIALS: {user}")
            
            sid = sio_events.get_user_sid(user)
            await sio_events.error_event(sid, "Invalid username or password")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # User is valid LDAPUser object
        token = auth_service.create_access_token(user)
        logger.info(f"TOKEN: {token}")
        logger.success("SUCCESSFULLY AUTHENTICATED USER")
        logger.debug(f"USER: {user}")
        
    except HTTPException:
        # Allow the to pass through to get more detailed error message
        raise
        
    except Exception as e:
        logger.error(f"EXCEPTION: {e}")
        sid = sio_events.get_user_sid(user)
        await sio_events.error_event(sid, f"Unexpected error during login {e}")
        
        logger.exception(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    
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
    # Get user sid
    sid = sio_events.get_user_sid(current_user)
    
    #!-PROGRESS TRACKING --------------------------------------------------------------
    if sid:
        await sio_events.start_toast(sid, 0)
    logger.debug("PROGRESS BAR: START TOAST EMITTED")
    
    download_tracker = create_download_tracker()
    download_tracker.start_download_tracking = True
    
    if sid:
        download_tracker.send_start_msg(sid)
        step_data = download_tracker.mark_step_done(DownloadStepName.VERIFY_FILE_EXISTS)
        if step_data:
            await sio_events.progress_update(sid, step_data)
    #!---------------------------------------------------------------------------------
    
    ID = payload.get("ID")
    if not ID:
        raise HTTPException(status_code=400, detail="ID is required")

    try:
        output_path = await pdf_service.create_pdf(
            ID=ID,
            db=db,
            payload=payload,
            current_user=current_user,
        )
        
        # Convert to Path object if it's a string
        if isinstance(output_path, str):
            output_path = Path(output_path)
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Statement of need form not found")

        # File does exists 
        if sid:
            step_data = download_tracker.mark_step_done(DownloadStepName.VERIFY_FILE_EXISTS)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
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
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    # Use the standard execute_search method
    from api.dependencies.pras_dependencies import get_search_service
    results = get_search_service().execute_search(query, db=None)
    logger.debug(f"RESULTS: {results}")
    
    logger.info(f"Search results for query '{query}': {len(results) if results else 0} items found")
    return JSONResponse(content=jsonable_encoder(results))

##########################################################################
## REBUILD SEARCH INDEX
##########################################################################
@api_router.post("/rebuildSearchIndex")
async def rebuild_search_index(
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """Rebuild the search index from scratch."""
    try:
        from api.dependencies.pras_dependencies import get_search_service
        get_search_service().rebuild_index()
        return {"message": "Search index rebuilt successfully"}
    except Exception as e:
        logger.error(f"Error rebuilding search index: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild search index: {str(e)}")

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
    current_user: LDAPUser = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    logger.debug(f"PAYLOAD JSON: {payload_json}")
    # Get user sid
    sid = sio_events.get_user_sid(current_user)
    
    #! PROGRESS TRACKING ---------------------------------------------------------
    await sio.emit("PROGRESS_UPDATE", {"event": "START_TOAST", "percent_complete": 0})
    logger.debug("PROGRESS BAR: START TOAST EMITTED")

    submit_request_tracker = create_submit_request_tracker()
    submit_request_tracker.start_submit_request_tracking = True
    
    if sid:
        submit_request_tracker.send_start_msg(sid)
        step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.REQUEST_STARTED)
        await sio_events.progress_update(sid, step_data)

    #!----------------------------------------------------------------------------
    """
    This endpoint:
      - Parses the incoming payload
      - Ensures the user is active via the LDAPUser we got from the token
      - Commits the request, tagging line items with current_user.username
    """
    try:
        payload: PurchaseRequestPayload = PurchaseRequestPayload.model_validate_json(payload_json)
        if sid:
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PAYLOAD_VALIDATED)
            if step_data:
                await sio_events.progress_update(sid, step_data)
            
    except ValidationError as e:
        error_details = e.errors()
        logger.error("PurchaseRequestPayload validation errors: %s", error_details)
        logger.error("Raw payload_json: %s", payload_json)  # Add this line
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
    if sid:
        step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.USER_AUTHENTICATED)
        await sio_events.progress_update(sid, step_data)
    logger.info("###########################################################")
    
    # Use current_user's email instead of doing another LDAP lookup to validate requester
    requester_email = current_user.email
    
    if not requester_email: 
        logger.error(f"Could not find email for user {current_user.username}")
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
    
    # Build header & line items inside a single transaction
    pdf_path: str | None = None
    async with db.begin():
        # Generate the purchase request ID
        # Subquery to find the maximum purchase_request_seq_id
        subq = (
            select(func.max(PurchaseRequestHeader.purchase_request_seq_id))
            .scalar_subquery()
        )
        
        # Outer query to get the row with that max seq ID
        stmt = (
            select(PurchaseRequestHeader.ID)
            .where(PurchaseRequestHeader.purchase_request_seq_id == subq)
        )
        result = await db.execute(stmt)
        purchase_req_id = result.scalar_one_or_none()
        
        #! PROGRESS TRACKING ----------------------------------------------------------
        if sid:
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PURCHASE_REQUEST_ID_GENERATED)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        #!-----------------------------------------------------------------------------
        
        ##################################################################################
        # UPDATING PR HEADER
        ##################################################################################
        logger.debug(f"PURCHASE REQUEST ID: {purchase_req_id}")
        
        # Check if IRQ1_ID already exists (if provided)
        if payload.irq1_id:
            # Check PurchaseRequestHeader table
            existing_pr_stmt = select(PurchaseRequestHeader).where(PurchaseRequestHeader.IRQ1_ID == payload.irq1_id)
            existing_pr_result = await db.execute(existing_pr_stmt)
            existing_pr = existing_pr_result.scalar_one_or_none()
            
            if existing_pr and existing_pr.ID != purchase_req_id:
                logger.warning(f"IRQ1_ID {payload.irq1_id} already exists for purchase request {existing_pr.ID}")
                raise HTTPException(status_code=409, detail=f"IRQ1_ID {payload.irq1_id} is already assigned to purchase request {existing_pr.ID}")
            
            # Check Approval table
            existing_approval_stmt = select(Approval).where(Approval.IRQ1_ID == payload.irq1_id)
            existing_approval_result = await db.execute(existing_approval_stmt)
            existing_approval = existing_approval_result.scalar_one_or_none()
            
            if existing_approval and existing_approval.purchase_request_id != purchase_req_id:
                logger.warning(f"IRQ1_ID {payload.irq1_id} already exists in approvals for purchase request {existing_approval.purchase_request_id}")
                raise HTTPException(status_code=409, detail=f"IRQ1_ID {payload.irq1_id} is already assigned to purchase request {existing_approval.purchase_request_id}")

        # Update Header table with rest of data
        stmt = (
			update(PurchaseRequestHeader)
			.where(PurchaseRequestHeader.ID == purchase_req_id)
			.values(
				IRQ1_ID=payload.irq1_id,
				requester=format_username(current_user.username),
				datereq=payload.items[0].datereq,
				orderType=payload.items[0].order_type,
				submission_status="SUBMITTED",
				created_time=utc_now_truncated()
			)
		)
        await db.execute(stmt)
        await db.flush()
        
        #! PROGRESS TRACKING ----------------------------------------------------------
        if sid:
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PR_HEADER_UPDATED)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        #!-----------------------------------------------------------------------------
        
        pr_line_item_uuids: List[str] = []
        uploaded_files: List[str] = []
        
        # Handle case where no files are provided
        files_list = []
        
        #?#################################################################################
        #? INSERTING THE LINE ITEMS TO DB
        #?#################################################################################
        for idx, item in enumerate(payload.items):
            file = files_list[idx] if idx < len(files_list) else None
            
            # Create line item
            orm_pr_line_item = PurchaseRequestLineItem(
                purchase_request_id=purchase_req_id,
                itemDescription=item.item_description,
                justification=item.justification,
                addComments="; ".join(item.additional_comments) if item.additional_comments else None,
                trainNotAval=item.train_not_aval,
                needsNotMeet=item.needs_not_meet,
                budgetObjCode=item.budget_obj_code,
                fund=item.fund,
                quantity=item.quantity,
                priceEach=item.price_each,
                originalPriceEach=item.price_each,
                totalPrice=item.total_price,
                location=item.location,
                isCyberSecRelated=item.is_cyber_sec_related,
                status=item.status,
                created_time=utc_now_truncated(),
            )
            db.add(orm_pr_line_item)
            await db.flush() # UUID is now available
            
            #! PROGRESS TRACKING ----------------------------------------------------------
            if sid:
                step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.LINE_ITEMS_INSERTED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)
            #!-----------------------------------------------------------------------------
            
            # #?#################################################################################
            # #? UPLOADING FILES IF USER ADDED ANY
            # #?#################################################################################
            # # Save uploaded file if exists
            # if file and file.filename:
            #     upload_dir = Path("uploads")
            #     upload_dir.mkdir(exist_ok=True)
                
            #     filename = f"{orm_pr_line_item.UUID}_{file.filename}"
            #     logger.debug(f"FILENAME: {filename}")
            #     full_path = upload_dir / filename
            #     logger.debug(f"FULL PATH: {full_path}")
                
            #     with open(full_path, "wb") as f:
            #         f.write(await file.read())
            #     logger.debug(f"FILE WRITTEN")
                    
            #     # Save file path to table in ORM model
            #     orm_pr_line_item.uploaded_file_path = str(full_path.resolve())
            #     uploaded_files.append(str(full_path.resolve()))
            #     logger.debug(f"UPLOADED FILES: {uploaded_files}")
            # UUID tracking
            pr_line_item_uuids.append(orm_pr_line_item.UUID)
            if sid:
                step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.FILES_UPLOADED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)
            
        #?#################################################################################
        #? SETTING THE CONTRACTING OFFICER
        #?#################################################################################
        # Get CO from purchase request headers
        stmt = (
            select(ContractingOfficer.username)
            .join(
                PurchaseRequestHeader,
                ContractingOfficer.id == PurchaseRequestHeader.contracting_officer_id
            )
            .where(PurchaseRequestHeader.ID == purchase_req_id)
        )
        result = await db.execute(stmt)
        contracting_officer_username = result.scalar_one_or_none()
        if sid:
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.CONTRACTING_OFFICER_RETRIEVED)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        logger.info(f"Contracting officer username: {contracting_officer_username}")
        
        #?#################################################################################
        #? INSERTING THE REQUEST INTO THE APPROVAL TABLE
        #?#################################################################################
        approvals: List[Approval] = []
        for item, line_uuid in zip(payload.items, pr_line_item_uuids):
            appr = Approval(
                UUID=str(uuid.uuid4()),
                purchase_request_id=purchase_req_id,
                requester=format_username(payload.requester),
                CO=contracting_officer_username,
                datereq=item.datereq,
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
            if sid:
                step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.APPROVAL_RECORDS_CREATED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)
            
            """
            Separating the requests based on the fund
            The 511x goes to IT (MATT STRONG)
            The 092x goes to "FINANCE" (LELA ROBICHAUX AND EDMUND BROWN)
            The MANAGEMENT requests could possibly never be sent to TED (EDWARD TAKARA), 
				if EDMUND (DEPUTY CLERK) can approve it (< $250)
            """
            if item.fund.startswith("511"):
                assigned_group = AssignedGroup.IT.value
            elif item.fund.startswith("092"):
                assigned_group = AssignedGroup.MANAGEMENT.value

            task = PendingApproval(
                purchase_request_id=purchase_req_id,
                line_item_uuid=line_uuid,
                approvals_uuid=appr.UUID,
                assigned_group=assigned_group,
                status=ItemStatus.NEW_REQUEST,
            )
            db.add(task)
            await db.flush()
            
            #! PROGRESS TRACKING ----------------------------------------------------------
            submit_request_tracker.mark_step_done(SubmitRequestStepName.PENDING_APPROVAL_INSERTED)
            #!-----------------------------------------------------------------------------
            
            stmt = select(PurchaseRequestHeader).where(PurchaseRequestHeader.ID == purchase_req_id)
            result = await db.execute(stmt)
            orm_pr_header = result.scalar_one_or_none()
            
            # Generate PDF once for the entire purchase request
            logger.info("Generating PDF document")
            if sid:
                step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_GENERATION_STARTED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)
                
                step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_TEMPLATE_LOADED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)
                
                step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_DATA_MERGED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)
            pdf_path: str = await generate_pdf(payload, orm_pr_header.ID, db, uploaded_files)
            
            
            #! PROGRESS TRACKING ----------------------------------------------------------
            if sid:
                step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_RENDERED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)
            #!-----------------------------------------------------------------------------
            
            orm_pr_header.pdf_output_path = pdf_path
    #* <--- transaction is committed here
    
    #?#########################################################################
    #?# EMAIL PAYLOADS
    #?#########################################################################
    attachments_list = []
    
    if pdf_path is not None:
        attachments_list.append(pdf_path)
        
    for path in uploaded_files:
        if path is not None:
            attachments_list.append(path)
            
    if sid:
        step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_SAVED_TO_DISK)
        if step_data:
            await sio_events.progress_update(sid, step_data)
            
    # Build kwargs dict for Pydantic, omitting attachments until confirmed present
    payload_kwargs = {
        "model_type": "email_request",
        "ID": purchase_req_id,
        "requester": payload.requester,
        "requester_email": requester_email,
        "datereq": payload.items[0].datereq,
        "orderType": payload.items[0].order_type,
        "subject": f"Purchase Request #{purchase_req_id}",
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
    # Make this to a condition, if this is a request from a requester, then we need to send it to the approvers
    # But we need to also send a confirmation to requester that is has been sent to the approvers
    """

    
    # Notify requester and approvers
    logger.info("Notifying requester and approvers")
    
    """
    If this is a IT request, send it to IT Approver (Matt) 
    If this is a non-IT request, send it to MANAGEMENT Approver (Lela)
    
    Finance creates the SON so the initial request will also need to be sent
    to Finance: Peter/Lauren
    
    This is the general route if starting with a Send to IT
    IT (Matt) -> Send to Managment (Edmund)
    Management (Edmund/Lela) -> Send to Clerk (Ted)
    Clerk -> Send to Financial (Lela)
    Financial -> Send to Procurement (Peter/Lauren)
    """
    
    #? Send request to approvers and requester
    send_to = None
    if payload.items[0].fund.startswith("511"):
        send_to = AssignedGroup.IT.value
    elif payload.items[0].fund.startswith("092"):
        send_to = AssignedGroup.MANAGEMENT.value
        
    logger.info(f"SENDING EMAILS {send_to}")
    async with asyncio.TaskGroup() as tg:
        
        # APPROVER
        #! PROGRESS TRACKING gets sent with task --------------------------------------------------
        tg.create_task(
            send_socket_data(
				step_name="send_approver_email",
				coro_fn=lambda: smtp_service.send_approver_email(
					email_request_payload, db, send_to
				)
			)
		)
        
        #! PROGRESS TRACKING gets sent with task --------------------------------------------------
        # REQUESTER
        tg.create_task(
			send_socket_data(
				step_name="send_requester_email",
				coro_fn=lambda: smtp_service.send_requester_email(
					email_request_payload, db=db
				)
			)
		)
        #!-----------------------------------------------------------------------------------------
    
    # Broadcast progress after both emails complete
    percent = submit_request_tracker.calculate_progress()
    send_data = {
        "event": "PROGRESS_UPDATE",
        "percent_complete": percent
    }
    await sio.emit("PROGRESS_UPDATE", send_data)
    
    #! PROGRESS TRACKING ----------------------------------------------------------
    # Mark final steps as done and broadcast final progress
    if sid:
        step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.EMAIL_PAYLOAD_BUILT)
        if step_data:
            await sio_events.progress_update(sid, step_data)
        
        step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.TRANSACTION_COMMITTED)
        if step_data:
            await sio_events.progress_update(sid, step_data)
        
        step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.REQUEST_COMPLETED)
        if step_data:
            await sio_events.progress_update(sid, step_data)
    # Calculate final progress and broadcast
    final_percent = submit_request_tracker.calculate_progress()
    final_send_data = {
        "event": "PROGRESS_UPDATE",
        "percent_complete": final_percent
    }  
    
    await sio.emit("PROGRESS_UPDATE", final_send_data)
    #!-----------------------------------------------------------------------------
    
    return JSONResponse({"message": "All work completed"})

#########################################################################
## SEND SOCKET DATA - send to frontend to update progress bar
#########################################################################
async def send_socket_data(
	step_name: str,
	coro_fn: Optional[Callable[P, Awaitable[R]]] = None,
	*args: P.args,
	**kwargs: P.kwargs
) -> Optional[R]:
    # Get the submit request tracker
    submit_request_tracker = get_submit_request_tracker()
    
    result: Optional[R] = None
    # If coroutine is given
    if coro_fn is not None:
        result = await coro_fn(*args, **kwargs)
        
    # Mark the step done based on the step_name
    if step_name == "send_approver_email":
        submit_request_tracker.mark_step_done(SubmitRequestStepName.APPROVER_EMAIL_SENT)
    elif step_name == "send_requester_email":
        submit_request_tracker.mark_step_done(SubmitRequestStepName.REQUESTER_EMAIL_SENT)

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

    # else:
    #     logger.bind(
    #         request_id=request_id,
    #         path=request.url.path,
    #         method=request.method,
    #         status_code=response.status_code,
    #         elapsed=elapsed,
    #     ).info("Request processed")

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
    sid = sio_events.get_user_sid(current_user.username)
    
    logger.info(f"Assigning requisition ID: {data.get('IRQ1_ID')}")
    user = format_username(current_user.username)
    
    try:
        # Only lela can assign RQ1 IDs
        if (user == CueClerk.MANAGER.value and current_user.has_group(LDAPGroup.CUE_GROUP.value)):
            logger.debug("AUTHORIZATION SUCCESSFUL")
            pass
        else:
            logger.debug("AUTHORIZATION FAILED")
            await sio_events.error_event(sid, "You are not authorized to assign requisition IDs")
            
            raise HTTPException(status_code=403, detail="You are not authorized to assign requisition IDs")
        
    except Exception as e:
        logger.error(f"Error assigning requisition ID: {e}")
        # Send error to frontend
        await sio_events.error_event(sid, f"Error assigning requisition ID: {e}")
        raise HTTPException(status_code=500, detail=f"Error assigning requisition ID: {e}")
    
    # Get the original ID from the request
    irq1_id = data.get('IRQ1_ID')
    original_id = data.get('ID')
    
    # Send error to frontend
    if not original_id or not irq1_id:
        await sio_events.error_event(sid, "Missing ID in request")
        raise HTTPException(status_code=400, detail="Missing ID in request")
    
    # Verify PurchaseRequestHeader exists
    stmt = select(PurchaseRequestHeader).where(PurchaseRequestHeader.ID == original_id)
    result = await db.execute(stmt)
    pr_header = result.scalar_one_or_none()
    
    if not pr_header:
        # Send error to frontend
        await sio_events.error_event(sid, "PurchaseRequestHeader not found")
        raise HTTPException(status_code=400, detail="PurchaseRequestHeader not found")
    
    # Check if IRQ1_ID already exists in PurchaseRequestHeader table
    existing_pr_stmt = select(PurchaseRequestHeader).where(PurchaseRequestHeader.IRQ1_ID == irq1_id)
    existing_pr_result = await db.execute(existing_pr_stmt)
    existing_pr = existing_pr_result.scalar_one_or_none()
    
    # Send error to frontend--------------------------------------------------------------------------------------------
    if existing_pr and existing_pr.ID != original_id:
        await sio_events.error_event(sid, f"IRQ1_ID {irq1_id} is already assigned to purchase request {existing_pr.ID}")
        logger.warning(f"IRQ1_ID {irq1_id} already exists for purchase request {existing_pr.ID}")
        raise HTTPException(status_code=409, detail=f"IRQ1_ID {irq1_id} is already assigned to purchase request {existing_pr.ID}")
    
    # Check if IRQ1_ID already exists in Approval table
    existing_approval_stmt = select(Approval).where(Approval.IRQ1_ID == irq1_id)
    existing_approval_result = await db.execute(existing_approval_stmt)
    existing_approval = existing_approval_result.scalar_one_or_none()
    
    # Send error to frontend--------------------------------------------------------------------------------------------
    if existing_approval and existing_approval.purchase_request_id != original_id:
        await sio_events.error_event(sid, f"IRQ1_ID {irq1_id} is already assigned to purchase request {existing_approval.purchase_request_id}")
        logger.warning(f"IRQ1_ID {irq1_id} already exists in approvals for purchase request {existing_approval.purchase_request_id}")
        raise HTTPException(status_code=409, detail=f"IRQ1_ID {irq1_id} is already assigned to purchase request {existing_approval.purchase_request_id}")
    
    try:
        # Update the IRQ1_ID
        await db.execute(
            update(PurchaseRequestHeader)
            .where(PurchaseRequestHeader.ID == original_id)
            .values(IRQ1_ID=irq1_id)
        )
        await db.commit()
        await db.refresh(pr_header)
        
        # Send success to frontend
        logger.success(f"Successfully assigned IRQ1_ID {irq1_id} to purchase request {original_id}")
        await sio_events.message_event(sid, f"Successfully assigned IRQ1_ID {irq1_id} to purchase request {original_id}")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error while assigning IRQ1_ID {irq1_id} to {original_id}: {e}")
        await sio_events.error_event(sid, f"Database error while assigning IRQ1_ID {irq1_id} to {original_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error while assigning IRQ1_ID: {str(e)}")
    
    return {"IRQ1_ID_ASSIGNED": True}

#########################################################################
## CHECK IRQ1_ID AVAILABILITY
##########################################################################
@api_router.get("/checkIRQ1_ID/{irq1_id}")
async def check_irq1_id_availability(
    irq1_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Check if an IRQ1_ID is available for assignment.
    Returns information about existing usage if found.
    """
    user = format_username(current_user.username)
    
    # Only authorized users can check IRQ1_ID availability
    if not ((user == CueClerk.MANAGER.value and current_user.has_group(LDAPGroup.CUE_GROUP.value)) 
            or user == CueClerk.TEST_USER.value):
        raise HTTPException(status_code=403, detail="You are not authorized to check IRQ1_ID availability")
    
    # Check PurchaseRequestHeader table
    pr_stmt = select(PurchaseRequestHeader).where(PurchaseRequestHeader.IRQ1_ID == irq1_id)
    pr_result = await db.execute(pr_stmt)
    existing_pr = pr_result.scalar_one_or_none()
    
    # Check Approval table
    approval_stmt = select(Approval).where(Approval.IRQ1_ID == irq1_id)
    approval_result = await db.execute(approval_stmt)
    existing_approval = approval_result.scalar_one_or_none()
    
    if existing_pr:
        return {
            "available": False,
            "message": f"IRQ1_ID {irq1_id} is already assigned to purchase request {existing_pr.ID}",
            "purchase_request_id": existing_pr.ID,
            "table": "purchase_request_headers"
        }
    
    if existing_approval:
        return {
            "available": False,
            "message": f"IRQ1_ID {irq1_id} is already assigned to purchase request {existing_approval.purchase_request_id}",
            "purchase_request_id": existing_approval.purchase_request_id,
            "table": "approvals"
        }
    
    return {
        "available": True,
        "message": f"IRQ1_ID {irq1_id} is available for assignment"
    }

#########################################################################
## ASSIGN CONTRACTING OFFICER
##########################################################################
@api_router.post("/assignCO")
async def assign_contracting_officer(
    payload: AssignCOPayload,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    # Add a create NEW ID call here, there could be instance where user
    # wants to send another request right after one
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
            
        elif row.submission_status == "SUBMITTED":
            purchase_req_id = await dbas.set_purchase_req_id(db=db)
            logger.info(f"New purchase request id: {purchase_req_id}")
            return {"ID": purchase_req_id}
        logger.info(f"ASSIGN CO PAYLOAD: {payload}")
        
    except Exception as e:
        logger.error(f"Error assigning CO: {e}")
        # Send error to frontend
        await sio.emit("ERROR", {"event": "ERROR", 
                                    "status_code": "500",
                                    "message": f"Error assigning CO: {e}"})
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
        # Send error to frontend
        await sio.emit("ERROR", {"event": "ERROR", 
                                    "status_code": "500",
                                    "message": f"Error denying request: {e}"})
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
    """
    Each step is going to enolve returning what step was completed and wrapped in sid to ensure sid is available 
    """
    try:
        logger.debug("APPROVE/DENY REQUEST")
        logger.debug(f"Current user: {current_user}")
        if current_user is None:
            logger.error("Current user is None - authentication failed")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        approval_tracker = create_approval_tracker()

        # Get the SocketIO session ID for the current user
        sid = sio_events.get_user_sid(current_user)

        # Mark steps (these functions should RETURN a dict, not emit)
        if sid:
            logger.debug(f"SID: {sid}")
            start_msg_data = approval_tracker.send_start_msg(sid)
            await sio_events.start_toast(sid, start_msg_data.get("percent_complete", 0))
            
            step_data = approval_tracker.mark_step_done(ApprovalStepName.APPROVAL_REQUEST_STARTED)
            if step_data:
                await sio_events.progress_update(sid, step_data)
            await asyncio.sleep(1)  # ✅ don't block the event loop
            
            step_data = approval_tracker.mark_step_done(ApprovalStepName.PAYLOAD_VALIDATED)
            if step_data:
                await sio_events.progress_update(sid, step_data)

        results = []
        for item_uuid, item_fund, total_price, target_status in zip(
            payload.UUID, payload.item_funds, payload.totalPrice, payload.target_status
        ):
            # Chain status checked
            # Check if already in approval chain with PENDING_APPROVAL status
            exists_stmt = select(
                exists().where(
                    PendingApproval.line_item_uuid == item_uuid,
                    PendingApproval.purchase_request_id == payload.ID,
                    PendingApproval.status == ItemStatus.PENDING_APPROVAL
                )
            )

            already_in_chain = await db.scalar(exists_stmt)
            
            if sid:
                step_data = approval_tracker.mark_step_done(ApprovalStepName.CHAIN_STATUS_CHECKED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)

            if already_in_chain:
                router = ApprovalRouter().start_handler(ClerkAdminHandler())
                # Mark skipped steps explicitly
                if sid:
                    for step in (
                        ApprovalStepName.IT_HANDLER_INITIALIZED,
                        ApprovalStepName.IT_APPROVAL_PROCESSED,
                        ApprovalStepName.MANAGEMENT_HANDLER_INITIALIZED,
                        ApprovalStepName.MANAGEMENT_APPROVAL_PROCESSED,
                    ):
                        step_data = approval_tracker.mark_step_done(step)
                        if step_data:
                            await sio_events.progress_update(sid, step_data)
            else:
                router = ApprovalRouter()  # full chain

            if sid:
                step_data = approval_tracker.mark_step_done(ApprovalStepName.ROUTER_CONFIGURED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)

            # Data retrieval
            stmt = select(
                PendingApproval.pending_approval_id,
                PendingApproval.assigned_group
            ).where(
                PendingApproval.line_item_uuid == item_uuid,
                PendingApproval.purchase_request_id == payload.ID
            )
            result = await db.execute(stmt)
            rows = result.all()
            
            if not rows:
                logger.error(f"No PendingApproval found for item_uuid: {item_uuid}, purchase_request_id: {payload.ID}")
                raise HTTPException(status_code=404, detail=f"No pending approval found for item {item_uuid}")
            
            if len(rows) > 1:
                logger.warning(f"Multiple PendingApproval records found for item_uuid: {item_uuid}, purchase_request_id: {payload.ID}. Using the first one.")
            
            # Use the first row if multiple are found
            
            row = rows[0]
            pending_approval_id = row.pending_approval_id
            assigned_group = row.assigned_group

            if sid:
                step_data = approval_tracker.mark_step_done(ApprovalStepName.PENDING_APPROVAL_DATA_RETRIEVED)
                if step_data:
                    await sio_events.progress_update(sid, step_data)

            # Debug current_user before using it
            logger.debug(f"Creating approval request - current_user: {current_user}")
            if current_user is None:
                logger.error("Current user is None when creating approval request")
                raise HTTPException(status_code=401, detail="Authentication required")
            
            approval_request = ApprovalRequest(
                id=payload.ID,
                uuid=item_uuid,
                pending_approval_id=pending_approval_id,
                fund=item_fund,
                status=target_status,
                total_price=total_price,
                action=payload.action,
                approver=current_user.username
            )

            if sid:
                step_data = approval_tracker.mark_step_done(ApprovalStepName.APPROVAL_REQUEST_BUILT)
                if step_data:
                    await sio_events.progress_update(sid, step_data)
            
            # Debug current_user before router call
            logger.debug(f"Before router.route - current_user: {current_user}")
            if current_user is None:
                logger.error("Current user is None before router.route call")
                raise HTTPException(status_code=401, detail="Authentication required")
            
            try:
                router_result = await router.route(approval_request, db, current_user, ldap_service)
            except Exception:
                logger.exception("router.route(...) failed: likely attempted .username on None or similar")
                raise

            ipc_data = await ipc_status.read()
            logger.debug(f"IPC STATUS: {ipc_data}")

            # If pending but email sent, finish progress UI
            if (ipc_data.request_pending and not ipc_data.request_approved) and ipc_data.approval_email_sent:
                if sid:
                    await sio_events.progress_update(sid, {
                        "event": "PROGRESS_UPDATE",
                        "percent_complete": 100,
                        "complete_steps": [
                            ApprovalStepName.REQUEST_MARKED_APPROVED.value,
                            ApprovalStepName.APPROVAL_EMAIL_SENT.value
                        ]
                    })

            results.append({
                "uuid": item_uuid,
                "status": getattr(router_result, "status", "processed").value if hasattr(router_result, "status") else "processed",
                "action": payload.action
            })

        return results

    except Exception as e:
        logger.exception("approve_deny_request failed")  # full traceback
        reset_signals()
        raise HTTPException(status_code=500, detail="Internal error while approving/denying request")
    
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
    createNewID is executed on startup to reserve a purchase_request_id,
    it also marks the end of the current request submission to the backend.
    
    The new id is inserted into the purchase_request_headers. Submissions are broken
    up for the most part into 2 sections. The Purchase Request Header and the Purchase
    Request Line Items. The actual table name is pr_line_items, and this is done to 
    allow for multiple items to be added to a request per submission. Once the request has
    successfully be submitted marked by SubmissionStatus.SUBMITTED ie. 'SUBMITTED' it is
    important to reset the shared_memory to continue progress tracking.
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
            
            # IN_PROGRESS -- return the last row ID
            if last_row_status == "IN_PROGRESS":
                stmt = (
                    select(
                        PurchaseRequestHeader.ID
                    )
                    .where(PurchaseRequestHeader.submission_status == "IN_PROGRESS")
                )
                result = await db.execute(stmt)
                last_row_id = result.scalar_one_or_none()
                return {"ID": last_row_id}
            
            # SUBMITTED or None -- create a new ID, we're at a new request
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
async def get_usernames(
    q: str = Query(..., min_length=1, description="Prefix to search"),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Return a list of username strings that start with the given prefix `q`.
    """
    return await ldap_service.fetch_usernames(q, current_user.username)

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
## UPDATE PRICE EACH/ TOTAL PRICE
##########################################################################
@api_router.post("/updatePrices")
async def update_prices(
    payload: UpdatePricesPayload,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Update the price each and total price for a purchase request line item.
    """
    logger.info(f"Updating prices for purchase request ID: {payload.purchase_request_id} and item UUID: {payload.item_uuid}")
    logger.debug(f"Payload: {payload}")
    
    # Grab original price each for item uuid
    stmt = select(
        PurchaseRequestLineItem.originalPriceEach).where(PurchaseRequestLineItem.UUID == payload.item_uuid)
    result = await db.execute(stmt)
    originalPriceEach = result.scalar_one_or_none()
    new_price_each = payload.new_price_each
    
    # Calculate 10% and $100 allowances
    price_allowance_ok = False
    
    try:
    # Allowance is ok if new price each is less than or equal to original price each + 10% or $100
        allowed_increase = min(originalPriceEach * 0.1, 100)
        price_allowance_ok = (new_price_each - originalPriceEach) <= allowed_increase
    except Exception as e:
        logger.error(f"Error calculating price allowance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Debug logging to help troubleshoot
    logger.info(f"PRICE UPDATE DEBUG:")
    logger.info(f"  Original Price Each: ${originalPriceEach}")
    logger.info(f"  New Price Each: ${new_price_each}")
    logger.info(f"  Price Difference: ${new_price_each - originalPriceEach}")
    logger.info(f"  Allowed Increase (10% or $100): ${allowed_increase}")
    logger.info(f"  Price Allowance OK: {price_allowance_ok}")
    logger.info(f"  Item Status: {payload.status}")
        
    logger.debug(f"UPDATED PRICES: {price_allowance_ok}")
    
    # Only allow updating prices for NEW_REQUEST or PENDING_APPROVAL statuses, not APPROVED or DENIED
    if (payload.status is not ItemStatus.DENIED) and price_allowance_ok:
        logger.info(f"payload: {payload}")
        stmt = (update(PurchaseRequestLineItem)
                .where(PurchaseRequestLineItem.purchase_request_id == payload.purchase_request_id)
                .where(PurchaseRequestLineItem.UUID == payload.item_uuid)
                .values(priceEach=payload.new_price_each, totalPrice=payload.new_total_price)
                .execution_options(synchronize_session="fetch")
        )
        
        await db.execute(stmt)
        await db.commit()
        logger.debug(f"Prices updated successfully")
        
        sid = sio_events.get_user_sid(current_user.username)
        await sio_events.message_event(sid, "Prices updated successfully")
        return {"message": "Prices updated successfully"}
    
    # If the price is too much or status is wrong, inform frontend
    sid = sio_events.get_user_sid(current_user.username)
    logger.debug(f"SID: {sid}")
    
    if not price_allowance_ok:
        await sio_events.error_event(sid, "Price allowance exceeded, must be less than or equal to original price each + 10% or $100")
        await sio_events.send_original_price(sid, originalPriceEach)
        
    raise HTTPException(status_code=500, detail="PRICE_ALLOWANCE_EXCEEDED")
   
##########################################################################
## UPDATE BOC, Location, or Fund
##########################################################################
@api_router.post("/boclocfund")
async def update_boclocfund(
    payload: UpdateBocLocFundPayload,
    db: AsyncSession = Depends(get_async_session),
    current_user: LDAPUser = Depends(auth_service.get_current_user)
):
    """
    Update the BOC, Location, or Fund for a purchase request line item.
    """
    logger.debug(f"Payload: {payload}")
    sid = sio_events.get_user_sid(current_user.username)
    
    budget_obj_code = payload.budgetObjCode
    fund = payload.fund
    
    # if updating fund or budgetobjcode, first check if compatible by checking budget_object_code table
    if budget_obj_code or fund:
        stmt = select(BudgetObjCode).where(BudgetObjCode.boc_code == budget_obj_code, BudgetObjCode.fund_code == fund)
        result = await db.execute(stmt)
        budget_obj_code_result = result.scalar_one_or_none()
        
        if not budget_obj_code_result:
            await sio_events.error_event(sid, "Budget Object Code or Fund is not compatible")
            raise HTTPException(status_code=400, detail="Budget Object Code or Fund is not compatible")
    
    # Update the BOC, Location, or Fund for the purchase request line item
    try:
        stmt = (update(PurchaseRequestLineItem)
                .where(PurchaseRequestLineItem.UUID == payload.item_uuid)
                .values(budgetObjCode=payload.budgetObjCode, location=payload.location, fund=payload.fund)
                .execution_options(synchronize_session="fetch")
            )
        
        await db.execute(stmt)
        await db.commit()
        await sio_events.message_event(sid, "BOC, Location, or Fund updated successfully")
        
        return {"message": "BOC, Location, or Fund updated successfully"}
            
    except Exception as e:
        await sio_events.error_event(sid, f"Error updating BOC, Location, or Fund: {e}")
        logger.error(f"Error updating BOC, Location, or Fund: {e}")
        raise HTTPException(status_code=500, detail=str(e))
  
##########################################################################
## HANDLE FILE UPLOAD
##########################################################################
@api_router.post("/uploadFile")
async def upload_file(
    ID: str = Form(...), 
    file: UploadFile = File(...), 
    current_user: LDAPUser = Depends(auth_service.get_current_user)):
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
# REGISTER ROUTES -- routes must be above this to be visible
##########################################################################
app.include_router(api_router)

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