from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import select
from sqlalchemy import (create_engine, String, Integer,
                         Float, Boolean, Text, LargeBinary, ForeignKey, DateTime, Enum)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.inspection import inspect
from sqlalchemy import Enum as SQLEnum
from contextlib import contextmanager
from typing import Optional
import uuid
import enum
import os

# Ensure database directory exists
db_dir = os.path.join(os.path.dirname(__file__), '..', 'db')
os.makedirs(db_dir, exist_ok=True)

# Create engine and base
engine = create_engine('sqlite:///api/db/pras.db', echo=False)  # PRAS = Purchase Request Approval System
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

###################################################################################################
##  LINE ITEM STATUS ENUMERATION
class ItemStatus(enum.Enum):
    NEW = "NEW REQUEST"  # This matches what's in your database
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ON_HOLD = "ON HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

###################################################################################################
## PURCHASE REQUEST
class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    UUID:            Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ID:              Mapped[str] = mapped_column(String, unique=False, nullable=False)
    requester:       Mapped[str] = mapped_column(String, nullable=False)
    phoneext:        Mapped[int] = mapped_column(Integer, nullable=False)
    datereq:         Mapped[str] = mapped_column(String)      
    dateneed:        Mapped[Optional[str]] = mapped_column(String, nullable=True)
    orderType:       Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fileAttachments: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    itemDescription: Mapped[str] = mapped_column(Text)
    justification:   Mapped[str] = mapped_column(Text)
    addComments:     Mapped[Optional[str]] = mapped_column(Text) 
    trainNotAval:    Mapped[bool] = mapped_column(Boolean, nullable=True)
    needsNotMeet:    Mapped[bool] = mapped_column(Boolean, nullable=True)
    budgetObjCode:   Mapped[str] = mapped_column(String)
    fund:            Mapped[str] = mapped_column(String)
    status:          Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus, 
                                                                name="item_status",
                                                                native_enum=False,
                                                                values_callable=lambda enum: [e.value for e in enum]
                                                                ),
                                                                default=ItemStatus.NEW
                                                            )
    priceEach:       Mapped[float] = mapped_column(Float)
    totalPrice:      Mapped[float] = mapped_column(Float)
    location:        Mapped[str] = mapped_column(String)
    quantity:        Mapped[int] = mapped_column(Integer)
    createdTime:     Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    __searchable__ = ['ID', 'IRQ1_ID', 'requester', 'budgetObjCode', 'fund',
                     'location', 'quantity', 'priceEach', 'totalPrice', 'status', 'trainNotAval', 'needsNotMeet']

    # Relationships
    approvals = relationship("Approval", back_populates="purchase_request", cascade="all, delete-orphan")

###################################################################################################
## approval TABLE
class Approval(Base):
    __tablename__ =  "approvals"
    __searchable__ = ['ID', 'IRQ1_ID', 'CO', 'requester', 'budgetObjCode', 'fund', 'trainNotAval', 'needsNotMeet',
                      'quantity', 'totalPrice', 'priceEach', 'location', 'newRequest', 
                      'approved', 'pendingApproval', 'status', 'createdTime', 'approvedTime', 'deniedTime']

    # Sequential ID for user-facing operations
    UUID:                   Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ID:                     Mapped[str] = mapped_column(String, nullable=False)
    IRQ1_ID:                Mapped[str] = mapped_column(String, nullable=True, unique=True)
    purchase_request_uuid:  Mapped[str] = mapped_column(String, ForeignKey("purchase_requests.UUID"), nullable=False)
    requester:              Mapped[str] = mapped_column(String, nullable=False)
    CO:                     Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phoneext:               Mapped[int] = mapped_column(Integer, nullable=False)
    datereq:                Mapped[str] = mapped_column(String)      
    dateneed:               Mapped[Optional[str]] = mapped_column(String, nullable=True)      
    orderType:              Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fileAttachments:        Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    itemDescription:        Mapped[str] = mapped_column(Text)
    justification:          Mapped[str] = mapped_column(Text)
    trainNotAval:           Mapped[bool] = mapped_column(Boolean, nullable=True)
    needsNotMeet:           Mapped[bool] = mapped_column(Boolean, nullable=True)
    budgetObjCode:          Mapped[str] = mapped_column(String)
    fund:                   Mapped[str] = mapped_column(String)
    priceEach:              Mapped[float] = mapped_column(Float)
    totalPrice:             Mapped[float] = mapped_column(Float)
    location:               Mapped[str] = mapped_column(String)
    quantity:               Mapped[int] = mapped_column(Integer)
    createdTime:            Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    isCyberSecRelated:      Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)   
    status:                 Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus, 
                                                                name="item_status",
                                                                native_enum=False,
                                                                values_callable=lambda enum: [e.value for e in enum]
                                                                ),
                                                                default=ItemStatus.NEW
                                                            )
    purchase_request = relationship("PurchaseRequest", back_populates="approvals")
    son_comments = relationship("SonComment", back_populates="approval", cascade="all, delete-orphan")
    line_item_statuses = relationship("LineItemStatus", back_populates="approval", cascade="all, delete-orphan")
 
###################################################################################################
## review TABLE
class LineItemStatus(Base):
    __tablename__ = "line_item_statuses"
    UUID:                   Mapped[str] = mapped_column(String, ForeignKey("approvals.UUID"), primary_key=True, nullable=False)
    status:                 Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus, name="item_status"),
                                                                        nullable=False,
                                                                        default=ItemStatus.NEW)
    created_at:             Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    hold_until:             Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_updated:           Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by:             Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updater_username:       Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updater_email:          Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationships
    approval = relationship("Approval", back_populates="line_item_statuses")

###################################################################################################
## LINE ITEM COMMENTS TABLE
class SonComment(Base):
    __tablename__ = "son_comments"
    
    UUID:               Mapped[str] = mapped_column(String, ForeignKey("approvals.UUID"), primary_key=True, nullable=False)
    comment_text:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:         Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)
    son_requester:      Mapped[str] = mapped_column(String, nullable=False)
    item_description:   Mapped[Optional[str]] = mapped_column(String, nullable=True)
    purchase_req_id:    Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationships
    approval = relationship("Approval", back_populates="son_comments")

###################################################################################################
## Finance Dept Members
###################################################################################################
class FinanceDeptMembers(Base):
    __tablename__ = "finance_dept_members"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
# TESTING: insert into finance_dept_members (id, username, email) values ('roman01', 'romancambell', 'roman_campbell@lawb.uscourts.gov');
###################################################################################################
## Request Approvers
###################################################################################################
class RequestApprovers(Base):
    __tablename__ = "request_approvers"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
# TESTING: insert into request_approvers (id, username, email) values ('roman01', 'romancambell', 'roman_campbell@lawb.uscourts.gov');

###################################################################################################
## Request Approvers
###################################################################################################
class ITDeptMembers(Base):
    __tablename__ = "it_dept_members"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)

##############################################################################   
## Get all data from Approval
def get_all_approval(db_session: Session):
    return db_session.query(Approval).all()

def get_approval_by_id(db_session: Session, ID: str):
    return db_session.query(Approval).filter(Approval.ID == ID).first()

###################################################################################################
# Insert data
def insert_data(table=None, data=None):
    # Get last id if there is one 
    logger.info(f"Inserting data into {table}: {data}")
    table = table.strip().lower() 
    
    if not data:
        raise ValueError("Data must be a non-empty dictionary")
    
    # Pick the right table
    match table:
        case "purchase_requests":
            model = PurchaseRequest
            pk_field = "UUID"
            
        case "approvals":
            model = Approval
            pk_field = "UUID"
            
        case "line_item_statuses":
            model = LineItemStatus
            pk_field = "UUID"
            
        case "son_comments":
            model = SonComment
            pk_field = "UUID"
            
        case _:
            raise ValueError(f"Unsupported table: {table}")
        
    # Strip out keys that are not in model
    valid_cols = set(inspect(model).columns.keys())
    filtered_data = {k: v for k, v in data.items() if k in valid_cols}
    
    with get_session() as session:
        obj = model(**filtered_data)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        logger.info(f"Inserted data into {table}")
        return obj

###################################################################################################
# Get status of request from Approval table
###################################################################################################
def get_status_by_id(db_session: Session, ID: str):
    logger.info(f"Fetching status for ID: {ID}")
    
    if not ID:
        raise ValueError("ID must be a non-empty string")
    
    # First try to find by sequential ID
    result = db_session.query(Approval).filter(Approval.ID == ID).first()
    if not result:
        # If not found, try uuid
        result = db_session.query(Approval).filter(Approval.uuid == ID).first()
    
    if result:
        return result.status
    else:
        logger.error(f"Object with ID {ID} not found in Approval table")
        raise ValueError(f"Object with ID {ID} not found in Approval table")
    
###################################################################################################
# Get requester from Approval table by uuid
###################################################################################################
def get_requester_by_UUID(db_session: Session, UUID: str):
    logger.info(f"Fetching requester for UUID: {UUID}")
    
    # Query the Approval table to get the requester field for the given uuid
    result = db_session.query(Approval.requester).filter(Approval.UUID == UUID).first()
    logger.info(f"Requester: {result}")
    
    if result:
        return result[0]  # Return just the requester string
    else:
        logger.warning(f"No requester found for UUID: {UUID}")
        return None

###################################################################################################
# uuid cache to improve performance
###################################################################################################
_uuid_cache = {}

###################################################################################################
# UPDATE DATA BY UUID
###################################################################################################
def update_data_by_uuid(uuid: str, table: str, **kwargs):
    # Get last id if there is one 
    logger.info(f"Updating data in {table}: {kwargs}")
    table = table.strip().lower() 
    
    if not kwargs:
        raise ValueError("Data must be a non-empty dictionary")
    
    # Pick the right table
    match table:
        case "purchase_requests":
            model = PurchaseRequest
            pk_field = "UUID"
            
        case "approvals":
            model = Approval
            pk_field = "UUID"
            
        case "line_item_statuses":
            model = LineItemStatus
            pk_field = "UUID"
            
        case "son_comments":
            model = SonComment
            pk_field = "UUID"
            
        case _:
            raise ValueError(f"Unsupported table: {table}")
        
    # Strip out keys (columns) that are not in model
    valid_cols = set(inspect(model).columns.keys())
    filtered_data = {k: v for k, v in kwargs.items() if k in valid_cols}
    
    with get_session() as session:
        # Filters incoming data by UUID for the table
        #Line Item Statuses needs to use approve_uuid 
        
        obj = session.query(model).filter(getattr(model, pk_field) == uuid).first()
        logger.info(f"GETATTR test: {getattr(model, pk_field)}")
        if not obj:
            raise ValueError(f"No record found with {pk_field} {uuid} in {table}")
            
        for key, value in filtered_data.items():
            setattr(obj, key, value)
            
        session.commit()
        session.refresh(obj)
        logger.info(f"Updated data in {table}")
        return obj

###################################################################################################
# Get uuid by ID with caching
def get_uuid_by_id_cached(db_session: Session, ID: str):
    """
    Get uuid by ID with caching for better performance.
    """
    # Check cache first
    if ID in _uuid_cache:
        logger.info(f"uuid cache hit for ID: {ID}")
        return _uuid_cache[ID]
    
    # If not in cache, get from database
    UUID = get_uuid_by_id(db_session, ID)
    
    # Store in cache if found
    if uuid:
        _uuid_cache[ID] = uuid
        logger.info(f"Added uuid to cache for ID: {ID}")
    
    return UUID

###################################################################################################
# Get uuid by ID
###################################################################################################
def get_uuid_by_id(db_session: Session, ID: str):
    result = db_session.query(Approval.UUID).filter(Approval.ID == ID).first()
    return result[0] if result else None
        
###################################################################################################
# Retrieve data from single line
###################################################################################################
def fetch_single_row(self, model_class, columns: list, condition, params: dict):
    """
    model_class: SQLAlchemy ORM model (e.g., PurchaseRequest)
    columns: list of attributes (e.g., [PurchaseRequest.requester, PurchaseRequest.fund])
    condition: SQLAlchemy filter expression (e.g., PurchaseRequest.IRQ1_ID == :req_id)
    params: dictionary of bind parameters (e.g., {"req_id": "REQ-001"})
    """
    
    if not columns or not isinstance(columns, list):
        raise ValueError("Columns must be a non-empty list")
    
    with get_session() as session:
        result = session.query(*columns).filter(condition).params(params).first()
        return result
    
###################################################################################################
# Get last 4 digits of the ID from the database
###################################################################################################
def _get_last_id() -> Optional[str]:
    """
    Return the full most‐recent PurchaseRequest.ID (e.g. "20250414-0007"),
    or None if the table is empty.
    """
    with get_session() as session:
        # Query the Approval table instead of PurchaseRequest
        row = (
            session.query(Approval.ID)
            .order_by(Approval.ID.desc())
            .limit(1)
            .first()
        )
        # Return just the ID string, not the tuple
        return row[0] if row else None
    
###################################################################################################
# Get next  request ID
###################################################################################################
def get_next_request_id() -> str:
    """
    Build the next ID in "YYYYMMDD-XXXX" format:
    - If today's date ≠ last ID's date, start at 0001
    - Otherwise increment the last 4‑digit suffix
    """
    first_section = "LAWB"
    last_id = _get_last_id()
    
    if not last_id:
        logger.info("No previous IDs found, starting with 0001")
        next_suffix = 1
    else:
        try:
           # Extract numeric suffix from last_id
           raw_suffix = last_id.replace(first_section, "")
           last_suffix = int(raw_suffix)
           next_suffix = last_suffix + 1
           logger.info(f"Last ID: {last_id}, next suffix: {next_suffix}")
        except ValueError:
            logger.warning(f"Invalid suffix in ID: {last_id}, starting with 0001")
            next_suffix = 1
        except Exception as e:
            logger.error(f"Error processing last ID: {e}, starting with 0001")
            next_suffix = 1
            
    suffix_str = f"{next_suffix:04d}"
    return first_section + suffix_str
            
            
###################################################################################################
# Get status of request from Approval table by uuid
###################################################################################################
def get_status_by_uuid(db_session: Session, uuid: str):
    logger.info(f"Fetching status for uuid: {uuid}")
    
    if not uuid:
        raise ValueError("uuid must be a non-empty string")
    
    result = db_session.query(Approval.status).filter(Approval.uuid == uuid).first()
    
    if result:
        return result[0]  # Return just the status string
    else:
        logger.warning(f"No status found for uuid: {uuid}")
        return None

###################################################################################################
# Get uuids for multiple IDs
###################################################################################################
def get_uuids_by_ids(db_session: Session, ids: list):
    """
    Get uuids for multiple IDs.
    Returns a dictionary mapping IDs to uuids.
    """
    logger.info(f"Getting uuids for {len(ids)} IDs")
    
    result = {}
    for id in ids:
        uuid = get_uuid_by_id(db_session, id)
        if uuid:
            result[id] = uuid
    
    return result

###################################################################################################
# GET USERNAMES
###################################################################################################
def get_usernames(db_session: Session, prefix: str):
    """
    Get usernames that start with the given prefix. FROM LDAPS NOT APPROVAL TABLE
    """
    return db_session.query(Approval.requester).filter(Approval.requester.like(f"{prefix}%")).all()

###################################################################################################
# CHECK STATUS VALUES
###################################################################################################
def check_status_values():
    """Check what status values exist in the database"""
    with get_session() as session:
        # Check approvals table
        approval_statuses = session.query(Approval.status).distinct().all()
        logger.info(f"Approval statuses: {approval_statuses}")
        
        # Check purchase_requests table
        pr_statuses = session.query(PurchaseRequest.status).distinct().all()
        logger.info(f"Purchase Request statuses: {pr_statuses}")
        
        # Check line_item_statuses table
        lis_statuses = session.query(LineItemStatus.status).distinct().all()
        logger.info(f"Line Item Statuses: {lis_statuses}")

###################################################################################################
# Get all purchase requests
###################################################################################################``
def get_all_purchase_requests(session):
    """Get all purchase requests from the database"""
    return session.query(PurchaseRequest).all()

###################################################################################################
# Get additional comments by ID
###################################################################################################
def get_additional_comments_by_id(ID: str):
    """Get additional comments by ID"""
    with get_session() as session:
        stmt = (
            select(PurchaseRequest.addComments)
            .join(Approval, PurchaseRequest.ID == Approval.ID)
            .where(PurchaseRequest.addComments.is_not(None))
            .where(PurchaseRequest.ID == ID)
        )
        additional_comments = session.scalars(stmt).all()
    return additional_comments

###################################################################################################
# Get approval by ID
###################################################################################################
def get_approval_by_id(session, ID):
    """Get approval by ID"""
    return session.query(Approval).filter(Approval.ID == ID).first()

# Create all tables
def init_db():
    """Initialize the database by creating all tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
# Call init_db to create tables
init_db()
