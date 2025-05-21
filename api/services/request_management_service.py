# Req Management Service for processing purchase requests
# approve/deny/follow up/comment all come here from the pras_api.py
from http.client import HTTPException
from loguru import logger
from sqlalchemy.orm import Session
from services.db_service import PurchaseRequest, Approval, LineItemStatus, SonComment
from services.email_service import EmailService
from pydantic_schemas import ItemStatus
from services.ldap_service import LDAPService, User
class RequestManagementService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def approve_deny_request(self, request_id: str, uuid: str, fund: str, action: str, requester: User):
        # Get request from db
        logger.info(f"Incoming request UUID: {uuid}/ID: {request_id}/Fund: {fund}/Action: {action}")
        request = self.get_request(request_id, uuid)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # MATCH ACTION -- This will determine what action to take based on current status
        # This will also send emails to the approvers and finance dept members
        # Order of ops is NEW -> finance dept -> PENDING -> approvers -> APPROVED/DENIED
        # Rule for Edmund Approval: Anything under $250, Edmund can approve
        # Rule for Ted Approval: Anything over $250, Ted must approve
        # If the fund is 511***, then NEW -> Matt Strong (IT) -> PENDING -> Ted -> APPROVED/DENIED
        # This is to ensure that the request is processed in the correct order
            
        match action:
            case "approve":
                # Check if the fund is 511***
                if request.status == ItemStatus.NEW:
                    logger.info(f"Request {request_id} is new")
                    # Check if the fund is 511***
                    # Send email to Matt Strong (IT) -- Roman for testing
                    group = get_routing_group(fund)
                    logger.info(f"Request {request_id} is being routed to {group}")
                    request.status = ItemStatus.PENDING
                    logger.info(f"Request {request_id} is now {request.status}")
                
                if request.status == ItemStatus.PENDING:
                    # check dollar amount
                    
                    
                    # Now send email to the approvers (Ted/Edmund)
                    
                    request.status = ItemStatus.APPROVED
                
            case "deny":
                logger.error(f"Request {request_id} denied")
                request.status = ItemStatus.DENIED
            case "follow_up":
                logger.warning(f"Request {request_id} on hold")
                request.status = ItemStatus.ON_HOLD
            case "cancel":
                logger.warning(f"Request {request_id} cancelled")
                request.status = ItemStatus.CANCELLED
            case "complete":
                logger.success(f"Request {request_id} completed")
                request.status = ItemStatus.COMPLETED
            case _:
                raise HTTPException(status_code=400, detail="Invalid action")

    def get_request(self, request_id: str, uuid: str):
        return self.db_session.query(Approval).filter(Approval.ID == request_id, Approval.UUID == uuid).first()



