from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from loguru import logger
from sqlalchemy import select
from sqlalchemy import (
    create_engine, 
    String, 
    Integer, 
    Date, 
    Float, 
    Boolean, 
    Text, 
    LargeBinary, 
    ForeignKey, 
    DateTime, 
    Enum as SAEnum, 
    JSON, 
    func,
    Enum as SQLEnum,
    literal,
    func,
    select,
    text
    )
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.inspection import inspect
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import List, Optional
import uuid
import enum
import os
import sqlite3


# Ensure database directory exists
db_dir = os.path.join(os.path.dirname(__file__), '..', 'db')
os.makedirs(db_dir, exist_ok=True)

# Create engine and base
engine = create_engine('sqlite:///api/db/pras.db', echo=True)  # PRAS = Purchase Request Approval System
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

DATABASE_URL_ASYNC = "sqlite+aiosqlite:///api/db/pras.db"
engine_async = create_async_engine(DATABASE_URL_ASYNC, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine_async, class_=AsyncSession)

# dependency to hand out AsyncSession instances
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

###################################################################################################
## Inbound/IngestStatus (incoming Approve/Deny Request)
""" 
Inbound/IngestStatus (incoming Approve/Deny Request) - this is keeping track of the actual processing of the request,
not the status of the request if it was approved or denied, etc...
"""
class InboundStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    ERROR = "ERROR"
    
###################################################################################################
##  LINE ITEM STATUS ENUMERATION
class ItemStatus(enum.Enum):
    NEW_REQUEST = "NEW REQUEST"  # This matches what's in your database
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ON_HOLD = "ON HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

###################################################################################################
## PURCHASE REQUEST - this is the top level purchase request, line items are added to this request
class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    id            = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id    = mapped_column(String, nullable=False, unique=True)
    uuid          = mapped_column(
                       String,
                       unique=True,
                       default=lambda: str(uuid.uuid4())
                    )
                      
    requester     = mapped_column(String, nullable=True)
    phoneext     = mapped_column(Integer, nullable=True)
    datereq= mapped_column(Date,  nullable=True)
    dateneed   = mapped_column(Date,  nullable=True)
    order_type    = mapped_column(String,nullable=True)
    status        = mapped_column(
                       SQLEnum(ItemStatus, name="item_status"),
                       default=ItemStatus.NEW_REQUEST,
                       nullable=True
                    )
    created_time  = mapped_column(
                       DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc),
                       nullable=False
                    )
    #---------------------------------------------------------------------
    # Relationships
    approvals           = relationship(
                             "Approval",
                             back_populates="purchase_requests",
                             cascade="all, delete-orphan"
                         )
    purchase_request_line_items = relationship(
                             "PurchaseRequestLineItem",
                             back_populates="purchase_requests",
                             cascade="all, delete-orphan"
                         )

    __searchable__ = [
        "request_id",
        "requester",
        "status",
        "created_time",
    ]
###################################################################################################
## Line Item Table
"""
Keeps track of the line items for the purchase request
"""
class PurchaseRequestLineItem(Base):
    __tablename__ = "purchase_request_line_items"

    id                      = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_request_uuid       = mapped_column(String, ForeignKey("purchase_requests.uuid"), nullable=False, index=True)
    item_description        = mapped_column(Text,   nullable=False)
    justification           = mapped_column(Text,   nullable=False)
    add_comments            = mapped_column(Text,   nullable=True)
    train_not_aval          = mapped_column(Boolean, default=False, nullable=False)
    needs_not_meet          = mapped_column(Boolean, default=False, nullable=False)
    budget_obj_code         = mapped_column(String, nullable=False)
    fund                    = mapped_column(String, nullable=False)
    quantity                = mapped_column(Integer,nullable=False)
    price_each              = mapped_column(Float,  nullable=False)
    total_price             = mapped_column(Float,  nullable=False)
    location                = mapped_column(String, nullable=False)
    is_cyber_sec_related    = mapped_column(Boolean, default=False, nullable=False)
    status                  = mapped_column(
                                 SQLEnum(ItemStatus, name="item_status"),
                                 default=ItemStatus.NEW_REQUEST,
                                 nullable=False
                             )
    created_time            = mapped_column(
                                 DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc),
                                 nullable=False
                             )

    #---------------------------------------------------------------------
    # ORM relationships
    purchase_requests = relationship(
        "PurchaseRequest",
        back_populates="purchase_request_line_items"
    )

    line_item_approvals = relationship(
        "LineItemApproval",
        back_populates="purchase_request_line_items",
        cascade="all, delete-orphan"
    )

    __searchable__ = [
        "id",
        "purchase_request_uuid",
        "item_description",
        "quantity",
        "price_each",
        "total_price",
        "status",
        "location",
    ]


###################################################################################################
## approval TABLE
"""
FOR READ ONLY PURPOSES WHEN LOOKING AT THE APPROVALS
"""
class Approval(Base):
    __tablename__ =  "approvals"
    __searchable__ = ['id', 'irq1_id', 'co', 'requester', 'budget_obj_code', 'fund', 'train_not_aval', 'needs_not_meet',
                      'quantity', 'total_price', 'price_each', 'location', 'new_request', 
                      'approved', 'pending_approval', 'status', 'created_time', 'approved_time', 'denied_time']

    # Sequential id for user-facing operations
    id:                     Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:                   Mapped[str] = mapped_column(String, default=lambda: str(uuid.uuid4()))
    irq1_id:                Mapped[str] = mapped_column(String, nullable=True, unique=True)
    purchase_request_uuid:      Mapped[str] = mapped_column(String, ForeignKey("purchase_requests.uuid"), nullable=False)
    purchase_request_id:        Mapped[str] = mapped_column(String, nullable=False)
    requester:              Mapped[str] = mapped_column(String, nullable=False)
    co:                     Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phoneext:               Mapped[int] = mapped_column(Integer, nullable=False)
    datereq:                Mapped[str] = mapped_column(String)      
    dateneed:               Mapped[Optional[str]] = mapped_column(String, nullable=True)      
    order_type:             Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_attachments:       Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    item_description:       Mapped[str] = mapped_column(Text)
    justification:          Mapped[str] = mapped_column(Text)
    train_not_aval:         Mapped[bool] = mapped_column(Boolean, nullable=True)
    needs_not_meet:         Mapped[bool] = mapped_column(Boolean, nullable=True)
    budget_obj_code:        Mapped[str] = mapped_column(String)
    fund:                   Mapped[str] = mapped_column(String)
    price_each:             Mapped[float] = mapped_column(Float)
    total_price:            Mapped[float] = mapped_column(Float)
    location:               Mapped[str] = mapped_column(String)
    quantity:               Mapped[int] = mapped_column(Integer)
    created_time:           Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    is_cyber_sec_related:   Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
     
    status:                 Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus, 
                                                                name="item_status",
                                                                native_enum=False,
                                                                values_callable=lambda enum: [e.value for e in enum]
                                                                ),
                                                                default=ItemStatus.NEW_REQUEST
                                                            )
    #---------------------------------------------------------------------
    # RELATIONSHIPS
    purchase_requests = relationship("PurchaseRequest", back_populates="approvals")
    son_comments = relationship("SonComment", back_populates="approvals", cascade="all, delete-orphan")
    line_item_approvals = relationship("LineItemApproval", back_populates="approvals", cascade="all, delete-orphan")
    approval_requests     = relationship("ApprovalRequest", back_populates="approvals", cascade="all, delete-orphan")

###################################################################################################
## Approval Event TABLE
"""
This is for incoming requests from an external system or webhook ("here's a JSON payload telling you to approve/deny").
"""
class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id:                 Mapped[int]        = mapped_column(Integer, primary_key=True)
    approvals_uuid:      Mapped[str]       = mapped_column(String, ForeignKey("approvals.uuid"), nullable=False)
    purchase_request_uuid:  Mapped[str]    = mapped_column(String, ForeignKey("purchase_requests.uuid"), nullable=False)
    action:             Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus), nullable=False)  # APPROVED / DENIED
    target_status:      Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus), nullable=False)
    co:                 Mapped[Optional[str]]= mapped_column(String, nullable=True)
    item_funds:         Mapped[str]        = mapped_column(String, nullable=False)
    total_price:        Mapped[float]      = mapped_column(Float, nullable=False)

    status:             Mapped[InboundStatus] = mapped_column(
                               SQLEnum(InboundStatus),
                               default=InboundStatus.PENDING,
                               nullable=False
                           )
    error_message:      Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:         Mapped[datetime]       = mapped_column(
                               DateTime(timezone=True),
                               default=lambda: datetime.now(timezone.utc),
                               nullable=False
                           )
    processed_at:       Mapped[Optional[datetime]] = mapped_column(
                               DateTime(timezone=True),
                               nullable=True
                           )

    # relationship back to Approval
    approvals = relationship("Approval", back_populates="approval_requests")

###################################################################################################
## Line Item Status TABLE
class LineItemApproval(Base):
    __tablename__ = "line_item_approvals"
    id            = mapped_column(Integer, primary_key=True)
    approvals_uuid = mapped_column(String, ForeignKey("approvals.uuid"))
    purchase_req_line_item_id  = mapped_column(Integer, ForeignKey("purchase_request_line_items.id"))
    approver      = mapped_column(String)
    decision      = mapped_column(SQLEnum(ItemStatus))
    comments      = mapped_column(Text, nullable=True)
    created_at    = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    #---------------------------------------------------------------------
    # RELATIONSHIPS
    purchase_request_line_items = relationship("PurchaseRequestLineItem", back_populates="line_item_approvals")
    approvals = relationship("Approval", back_populates="line_item_approvals")

###################################################################################################
## LINE ITEM COMMENTS TABLE
class SonComment(Base):
    __tablename__ = "son_comments"
    
    id:                 Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approvals_uuid:      Mapped[str] = mapped_column(String, ForeignKey("approvals.uuid"), nullable=False)
    purchase_request_id:   Mapped[Optional[str]] = mapped_column(String, nullable=True)
    comment_text:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:         Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)
    son_requester:      Mapped[str] = mapped_column(String, nullable=False)
    item_description:   Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    #---------------------------------------------------------------------
    # RELATIONSHIPS
    approvals = relationship("Approval", back_populates="son_comments")

###################################################################################################
## USERS TABLE  -- TESTING ONLY
###################################################################################################
class Users(Base):
    __tablename__ = "users"
    id:         Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username:   Mapped[str] = mapped_column(String)
    email:      Mapped[str] = mapped_column(String)
    department: Mapped[str] = mapped_column(String)
    


##############################################################################   
## Get all data from Approval
def get_all_approval(db_session: Session):
    return db_session.query(Approval).all()

def get_approval_by_id(db_session: Session, id: str):
    return db_session.query(Approval).filter(Approval.id == id).first()

###################################################################################################
# Get status of request from Approval table
###################################################################################################
def get_status_by_id(db_session: Session, id: str):
    logger.info(f"Fetching status for id: {id}")
    
    if not id:
        raise ValueError("id must be a non-empty string")
    
    # First try to find by sequential id
    result = db_session.query(Approval).filter(Approval.id == id).first()
    if not result:
        # If not found, try uuid
        result = db_session.query(Approval).filter(Approval.uuid == id).first()
    
    if result:
        return result.status
    else:
        logger.error(f"Object with id {id} not found in Approval table")
        raise ValueError(f"Object with id {id} not found in Approval table")
    
###################################################################################################
# Get requester from Approval table by uuid
###################################################################################################
def get_requester_by_uuid(db_session: Session, uuid: str):
    logger.info(f"Fetching requester for uuid: {uuid}")
    
    # Query the Approval table to get the requester field for the given uuid
    result = db_session.query(Approval.requester).filter(Approval.uuid == uuid).first()
    logger.info(f"Requester: {result}")
    
    if result:
        return result[0]  # Return just the requester string
    else:
        logger.warning(f"No requester found for uuid: {uuid}")
        return None

###################################################################################################
# uuid cache to improve performance
###################################################################################################
_uuid_cache = {}

###################################################################################################
# UPDATE DATA BY uuid
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
            pk_field = "uuid"
            
        case "approvals":
            model = Approval
            pk_field = "uuid"
    
        case "son_comments":
            model = SonComment
            pk_field = "id"
            
        case _:
            raise ValueError(f"Unsupported table: {table}")
        
    # Strip out keys (columns) that are not in model
    valid_cols = set(inspect(model).columns.keys())
    filtered_data = {k: v for k, v in kwargs.items() if k in valid_cols}
    
    with get_session() as session:
        # Filters incoming data by uuid for the table
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
# Get uuid by id with caching
def get_uuid_by_id_cached(db_session: Session, id: str):
    """
    Get uuid by id with caching for better performance.
    """
    # Check cache first
    if id in _uuid_cache:
        logger.info(f"uuid cache hit for id: {id}")
        return _uuid_cache[id]
    
    # If not in cache, get from database
    uuid = get_uuid_by_id(db_session, id)
    
    # Store in cache if found
    if uuid:
        _uuid_cache[id] = uuid
        logger.info(f"Added uuid to cache for id: {id}")
    
    return uuid

###################################################################################################
# Get uuid by id
###################################################################################################
def get_uuid_by_id(db_session: Session, id: str):
    result = db_session.query(Approval.uuid).filter(Approval.id == id).first()
    return result[0] if result else None
        
###################################################################################################
# Retrieve data from single line
###################################################################################################
def fetch_single_row(self, model_class, columns: list, condition, params: dict):
    """
    model_class: SQLAlchemy ORM model (e.g., PurchaseRequest)
    columns: list of attributes (e.g., [PurchaseRequest.requester, PurchaseRequest.fund])
    condition: SQLAlchemy filter expression (e.g., PurchaseRequest.IRQ1_id == :req_id)
    params: dictionary of bind parameters (e.g., {"req_id": "REQ-001"})
    """
    
    if not columns or not isinstance(columns, list):
        raise ValueError("Columns must be a non-empty list")
    
    with get_session() as session:
        result = session.query(*columns).filter(condition).params(params).first()
        return result
    
###################################################################################################
# Get next  request id
###################################################################################################
def set_purchase_req_id() -> str:
    
    first_prefix = "LAWB"
    # Create next id for incoming purchase request
    try:
        with get_session() as session:
            stmt = select(
                (func.coalesce(func.max(PurchaseRequest.id), literal(0)) + 1).label("next_id")
            ).select_from(PurchaseRequest)
            next_int_id = session.execute(stmt).scalar_one()
            next_id = f"{first_prefix}{str(next_int_id).zfill(4)}"
            logger.info(f"Next purchase request id: {next_id}")
            return next_id
    except Exception as e:
        logger.error(f"Error setting purchase request id: {e}")
        return None
            
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
# Get uuids for multiple ids
###################################################################################################
def get_uuids_by_ids(db_session: Session, ids: list):
    """
    Get uuids for multiple ids.
    Returns a dictionary mapping ids to uuids.
    """
    logger.info(f"Getting uuids for {len(ids)} ids")
    
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
        


###################################################################################################
# Get all purchase requests
###################################################################################################``
def get_all_purchase_requests(session):
    """Get all purchase requests from the database"""
    return session.query(PurchaseRequest).all()

###################################################################################################
# Get additional comments by id
###################################################################################################
def get_add_comments_by_id(id: str):
    """Get additional comments by id"""
    with get_session() as session:
        stmt = (
            select(PurchaseRequest.add_comments)
            .join(Approval, PurchaseRequest.id == Approval.id)
            .where(PurchaseRequest.add_comments.is_not(None))
            .where(PurchaseRequest.id == id)
        )
        add_comments = session.scalars(stmt).all()
        return add_comments

###################################################################################################
# Get order_types
###################################################################################################
def get_order_types(id: str):
    """Get order_types by id"""
    with get_session() as session:
        stmt = (
            select(PurchaseRequest.order_type)
            .join(Approval, PurchaseRequest.id == Approval.id)
            .where(PurchaseRequest.order_type.is_not(None))
            .where(PurchaseRequest.id == id)
        )
        order_types = session.scalars(stmt).first()
    return order_types

###################################################################################################
# Get approval by id
###################################################################################################
def get_approval_by_id(session, id):
    """Get approval by id"""
    return session.query(Approval).filter(Approval.id == id).first()
    
# Call init_db to create tables on startup
def init_db():
    """Initialize the database by creating all tables."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Add request_id column if it doesn't exist
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(purchase_requests)"))
            columns = [row[1] for row in result]
            
            if 'request_id' not in columns:
                conn.execute(text("ALTER TABLE purchase_requests ADD COLUMN request_id VARCHAR"))
                conn.commit()
                
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

