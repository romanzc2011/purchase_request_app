from datetime import datetime, timezone
from http.client import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from loguru import logger
from aiocache import Cache, cached
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
    text,
    )
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base, selectinload, aliased
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.inspection import inspect
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import List, Optional
import uuid
import enum
import os

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
async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as async_session:
        yield async_session

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@staticmethod
def utc_now_truncated() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=0)

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
    
class TaskStatus(enum.Enum):
    NEW         = "NEW"
    PENDING     = "PENDING"
    PROCESSED   = "PROCESSED"
    ERROR       = "ERROR"
    CANCELLED   = "CANCELLED"

###################################################################################################
## PURCHASE REQUEST
class PurchaseRequestHeader(Base):
    __tablename__ = "purchase_request_headers"

    UUID:            Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ID:              Mapped[str] = mapped_column(String, unique=True, nullable=False)
    requester:       Mapped[str] = mapped_column(String, nullable=False)
    phoneext:        Mapped[int] = mapped_column(Integer, nullable=False)
    datereq:         Mapped[str] = mapped_column(String)      
    dateneed:        Mapped[Optional[str]] = mapped_column(String, nullable=True)
    orderType:       Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status        = mapped_column(
        SQLEnum(
            ItemStatus,
            name="item_status",
            native_enum=False,
            values_callable=lambda enum: [e.value for e in enum]
        ),
        default=ItemStatus.NEW,
        nullable=False
    )
    created_time  = mapped_column(
        DateTime(timezone=True),
        default=utc_now_truncated,
        nullable=False
    )

	#---------------------------------------------------------------------
	# Relationships
	#---------------------------------------------------------------------
    # Relationship back to Approval
    approvals = relationship(
        "Approval",
        back_populates ="purchase_request", 
        cascade="all, delete-orphan", 
        foreign_keys=lambda: [Approval.purchase_request_uuid]
    )
    pending_approvals = relationship(
        "PendingApproval", 
        back_populates="purchase_request", 
        cascade="all, delete-orphan", 
        foreign_keys=lambda: [PendingApproval.purchase_request_uuid]
    )
    line_items = relationship(
		"PurchaseRequestLineItem",
		back_populates="purchase_request",
		cascade="all, delete-orphan",
        foreign_keys=lambda: [PurchaseRequestLineItem.purchase_request_uuid]
	)
    

    __searchable__ = [
        "request_id",
        "requester",
        "status",
        "created_time",
    ]
    
#--------------------------------------------------------------------------------------------------
## PURCHASE REQUEST LINE ITEM TABLE
#--------------------------------------------------------------------------------------------------
class PurchaseRequestLineItem(Base):
    __tablename__ = "pr_line_items"
    UUID: 				Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    PR_HEADER_UUID: 	Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.UUID"), nullable=False)
    itemDescription: 	Mapped[str] = mapped_column(Text)
    justification: 		Mapped[str] = mapped_column(Text)
    addComments:     	Mapped[Optional[str]] = mapped_column(Text) 
    trainNotAval:    	Mapped[bool] = mapped_column(Boolean, nullable=True)
    needsNotMeet:    	Mapped[bool] = mapped_column(Boolean, nullable=True)
    budgetObjCode:   	Mapped[str] = mapped_column(String)
    fund:            	Mapped[str] = mapped_column(String)
    quantity: 			Mapped[int] = mapped_column(Integer)
    priceEach: 			Mapped[float] = mapped_column(Float)
    totalPrice: 		Mapped[float] = mapped_column(Float)
    location: 			Mapped[str] = mapped_column(String)
    status: 			Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus, 
                                                                name="item_status",
                                                                native_enum=False,
                                                                values_callable=lambda enum: [e.value for e in enum]
                                                                ),
                                                                default=ItemStatus.NEW
                                                            )
    createdTime: 		Mapped[datetime] = mapped_column(DateTime, default=utc_now_truncated, nullable=False)
    
    #---------------------------------------------------------------------
	# Relationships
	#---------------------------------------------------------------------
    # Relationship back to PurchaseRequestHeader
    purchase_request = relationship(
        "PurchaseRequest",
        back_populates="pr_line_items",
        foreign_keys=[PR_HEADER_UUID]
    )

    pending_approvals = relationship(
        "PendingApproval",
        back_populates="pr_line_item",
        cascade="all, delete-orphan",
    )
    
    line_item_approvals = relationship(
        "LineItemApproval",
        back_populates="pr_line_items",
        cascade="all, delete-orphan",
    )
    
    __searchable__ = [
        "id",
        "uuid",
        "purchase_request_uuid",
        "item_description",
        "quantity",
        "price_each",
        "total_price",
        "status",
        "location",
    ]

#--------------------------------------------------------------------------------------------------
## PURCHASE REQUEST APPROVAL TABLE
#--------------------------------------------------------------------------------------------------
class Approval(Base):
    __tablename__ =  "approvals"
    __searchable__ = ['ID', 'IRQ1_ID', 'CO', 'requester', 'budgetObjCode', 'fund', 'trainNotAval', 'needsNotMeet',
                      'quantity', 'totalPrice', 'priceEach', 'location', 'newRequest', 
                      'approved', 'pendingApproval', 'status', 'createdTime', 'approvedTime', 'deniedTime']

    # Sequential ID for user-facing operations
    UUID:                   Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ID:                     Mapped[str] = mapped_column(String, nullable=False)
    IRQ1_ID:                Mapped[str] = mapped_column(String, nullable=True, unique=True)
    purchase_request_uuid:  Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.UUID"), nullable=False)
    pr_line_items_uuid:     Mapped[str] = mapped_column(String, ForeignKey("pr_line_items.UUID"), nullable=False)
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
    createdTime:            Mapped[datetime] = mapped_column(DateTime, default=utc_now_truncated, nullable=False)
    isCyberSecRelated:      Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)   
    status:                 Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus, 
                                                                name="item_status",
                                                                native_enum=False,
                                                                values_callable=lambda enum: [e.value for e in enum]
                                                                ),
                                                                default=ItemStatus.NEW
                                                            )
    #---------------------------------------------------------------------
    # Relationships
    #---------------------------------------------------------------------
    purchase_request = relationship(
        "PurchaseRequestHeader",
        back_populates="approvals",
        foreign_keys=[purchase_request_uuid]
    )

    # SonComments point at approvals.uuid via their approvals_uuid column
    son_comments = relationship(
        "SonComment",
        back_populates="approvals",
        cascade="all, delete-orphan",
        foreign_keys="[SonComment.approvals_uuid]"
    )

    # LineItemApproval has its own approvals_uuid FK
    line_item_approvals = relationship(
        "LineItemApproval",
        back_populates="approvals",
        cascade="all, delete-orphan",
        foreign_keys="[LineItemApproval.approvals_uuid]"
    )

    # PendingApproval typically points at approvals.id or .uuid — adjust as needed
    pending_approvals = relationship(
        "PendingApproval",
        back_populates="approval",
        cascade="all, delete-orphan",
        foreign_keys=lambda: [PendingApproval.approval_uuid]
    )
 
###################################################################################################
## review TABLE
class LineItemApproval(Base):
    __tablename__ = "line_item_approvals"
    # keep this as your PK so front-end code still sees one "approval UUID"
    approval_uuid:    Mapped[str] = mapped_column(
        String,
        ForeignKey("approvals.UUID"),
        primary_key=True,
    )
    pr_line_item_uuid:Mapped[str] = mapped_column(
        String,
        ForeignKey("pr_line_items.UUID"),
        primary_key=True,
    )
    approver      = mapped_column(String, nullable=False)
    status        = mapped_column(SQLEnum(ItemStatus), nullable=False)
    decision      = mapped_column(SQLEnum(ItemStatus), nullable=False)
    created_at    = mapped_column(DateTime, default=utc_now_truncated, nullable=False)
    
    # Relationships
    approval = relationship("Approval", foreign_keys=[approval_uuid], back_populates="line_item_approval")
    line_items = relationship("PurchaseRequestLineItem", foreign_keys=[pr_line_item_uuid], back_populates="line_item_approval")
    
###################################################################################################
## PENDING APPROVAL TABLE
class PendingApproval(Base):
    __tablename__ = "pending_approvals"
    """
    This is more of a workflow table, it tracks the status of the approval process for a single line item.
    Decisions made with this table for example is what group based on fund etc...
    """
    task_id:Mapped[int] 	      = mapped_column(Integer, primary_key=True, autoincrement=True)
    pr_uuid:           Mapped[str] = mapped_column(
                            String,
                            ForeignKey("purchase_request_headers.UUID"),
                            nullable=False,
                            index=True,
                        )
    pr_line_item_uuid: Mapped[str] = mapped_column(
                            String,
                            ForeignKey("pr_line_items.UUID"),
                            nullable=True,
                            index=True,
                        )
    approval_uuid:     Mapped[str] = mapped_column(
                            String,
                            ForeignKey("approvals.UUID"),
                            nullable=True,
                            index=True,
                        )
    assigned_group:Mapped[str] 	  = mapped_column(String, nullable=False)

    # workflow‐status enum
    status:Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.NEW, nullable=False)
    
    # What the approver decided
    action = mapped_column(
        SQLEnum(
            name="item_status",
            native_enum=False, 
            values_callable=lambda enum: [e.value for e in enum]
            ),
        default=ItemStatus.NEW,
        nullable=False)
    
    # Task status
    task_status:Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        name="task_status",
        native_enum=False,
        values_callable=lambda enum: [e.value for e in enum],
        default=TaskStatus.NEW,
        nullable=False)
    
    # Timestamps, error info, etc.
    created_at                 = mapped_column(
        DateTime(timezone=True),
        default=utc_now_truncated,
        nullable=False
    )
    processed_at               = mapped_column(
        DateTime(timezone=True),
        default=utc_now_truncated,
        nullable=True
    )
    error_message              = mapped_column(Text, nullable=True)

	#-------------------------------------------------------------------------------------
    # relationships
    #-------------------------------------------------------------------------------------
    purchase_request: Mapped[PurchaseRequestHeader] = relationship(
        "PurchaseRequestHeader",
        back_populates="pending_approvals",
        foreign_keys=[pr_uuid],
    )
    line_items:      Mapped[PurchaseRequestLineItem] = relationship(
        "PurchaseRequestLineItem",
        back_populates="pending_approvals",
        foreign_keys=[pr_line_item_uuid],
    )
    approval:          Mapped[Approval] = relationship(
        "Approval",
        back_populates="pending_approvals",
        foreign_keys=[approval_uuid],
    )

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
## SEEDING JUSTIFICATION TEMPLATES
###################################################################################################
# Justification ORM model - singleton table for justification text
class JustificationTemplate(Base):
    __tablename__ = "justification_templates"
    code        = mapped_column(String, primary_key=True)
    description = mapped_column(
        Text, 
        nullable=False)
    
# Seed justification templates
async def seed_justification_templates(async_session: AsyncSession):
    # Only insert if empty
    existing = await async_session.execute(select(JustificationTemplate).limit(1))
    if existing.scalars().first():
        return
    
    templates = [
		JustificationTemplate(
			code="NOT_AVAILABLE",
			description="No comparable programs listed on approved sites."
		),
		JustificationTemplate(
			code="DOESNT_MEET_NEEDS",
			description="Current offerings do not meet the needs of the requester."
		),
	]
    async_session.add_all(templates)
    await async_session.commit()

# After table creation, seed the table with the following data:
# Create cache to store justification text
cache = Cache(Cache.MEMORY)

# Help function to fetch and cache justification text
@cached(ttl=300, cache=Cache.MEMORY, key="justification_templates")
async def get_justification_templates(async_session: AsyncSession) -> dict[str, str]:
    """
    Returns a dictionary mapping code -> template
    Cached in memory every 5minutes
    """
    result = await async_session.execute(select(JustificationTemplate))
    rows = result.scalars().all()
    return {r.code: r.description for r in rows}

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
            model = PurchaseRequestHeader
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
            model = PurchaseRequestHeader
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
def get_status_by_uuid(db_session: Session, UUID: str):
    logger.info(f"Fetching status for uuid: {UUID}")
    
    if not UUID:
        raise ValueError("UUID must be a non-empty string")
    
    result = db_session.query(Approval.status).filter(Approval.UUID == UUID).first()
    
    if result:
        return result[0]  # Return just the status string
    else:
        logger.warning(f"No status found for UUID: {UUID}")
        return None

###################################################################################################
# Get uuids for multiple IDs
###################################################################################################
def get_uuids_by_ids(db_session: Session, IDs: list):
    """
    Get uuids for multiple IDs.
    Returns a dictionary mapping IDs to uuids.
    """
    logger.info(f"Getting uuids for {len(IDs)} IDs")
    
    result = {}
    for ID in IDs:
        uuid = get_uuid_by_id(db_session, ID)
        if uuid:
            result[ID] = uuid
    
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
        pr_statuses = session.query(PurchaseRequestHeader.status).distinct().all()
        logger.info(f"Purchase Request statuses: {pr_statuses}")
        
        # Check line_item_statuses table
        lis_statuses = session.query(LineItemStatus.status).distinct().all()
        logger.info(f"Line Item Statuses: {lis_statuses}")

###################################################################################################
# Get all purchase requests
###################################################################################################``
def get_all_purchase_requests(session):
    """Get all purchase requests from the database"""
    return session.query(PurchaseRequestHeader).all()

###################################################################################################
# Get additional comments by ID
###################################################################################################
def get_additional_comments_by_id(ID: str):
    """Get additional comments by ID"""
    with get_session() as session:
        stmt = (
            select(PurchaseRequestLineItem.addComments)
            .join(Approval, PurchaseRequestHeader.ID == Approval.ID)
            .where(PurchaseRequestLineItem.addComments.is_not(None))
            .where(PurchaseRequestHeader.ID == ID)
        )
        additional_comments = session.scalars(stmt).all()
    return additional_comments

###################################################################################################
# Get orderTypes
###################################################################################################
def get_order_types(ID: str):
    """Get order types by ID"""
    with get_session() as session:
        stmt = (
            select(PurchaseRequestHeader.orderType)
            .join(Approval, PurchaseRequestHeader.ID == Approval.ID)
            .where(PurchaseRequestHeader.orderType.is_not(None))
            .where(PurchaseRequestHeader.ID == ID)
        )
        order_types = session.scalars(stmt).first()
    return order_types

###################################################################################################
# Get next  request id
###################################################################################################
def set_purchase_req_id() -> str:
    
    first_prefix = "LAWB"
    # Create next id for incoming purchase request
    try:
        with get_session() as session:
            stmt = select(
                (func.coalesce(func.max(PurchaseRequestHeader.ID), literal(0)) + 1).label("next_id")
            ).select_from(PurchaseRequestHeader)
            next_int_id = session.execute(stmt).scalar_one()
            next_id = f"{first_prefix}{str(next_int_id).zfill(4)}"
            logger.info(f"Next purchase request id: {next_id}")
            return next_id
    except Exception as e:
        logger.error(f"Error setting purchase request id: {e}")
        return None

###################################################################################################
# Get approval by ID
###################################################################################################
def get_approval_by_id(session, ID):
    """Get approval by ID"""
    return session.query(Approval).filter(Approval.ID == ID).first()

# Call init_db to create tables on startup
def init_db():
    """Initialize the database by creating all tables."""
    try:
        # Create (sync) all tables
        Base.metadata.create_all(bind=engine)
        
        # Seed justification templates
        with SessionLocal() as session:
            if not session.query(JustificationTemplate).first():
                logger.info("Seeding justification templates")
                session.add_all([
                    JustificationTemplate(
                        code="NOT_AVAILABLE",
                        description="No comparable programs listed on approved sites."
                    ),
                    JustificationTemplate(
                        code="DOESNT_MEET_NEEDS",
                        description="Current offerings do not meet the needs of the requester."
                    ),
                ])
                session.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    
# Call init_db to create tables
init_db()
