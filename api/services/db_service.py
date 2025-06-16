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
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)
    
###################################################################################################
##  LINE ITEM STATUS ENUMERATION
class ItemStatus(enum.Enum):
    NEW_REQUEST = "NEW REQUEST" 
    PENDING     = "PENDING APPROVAL"
    APPROVED    = "APPROVED"
    DENIED      = "DENIED"
    ON_HOLD     = "ON HOLD"
    COMPLETED   = "COMPLETED"
    CANCELLED   = "CANCELLED"

###################################################################################################
## PURCHASE REQUEST - this is the top level purchase request, line items are added to this request
class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    id            = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id    = mapped_column(String, nullable=False, unique=True)
    uuid          = mapped_column(String, unique=True, default=lambda: str(uuid.uuid4()))
    irq1_id       = mapped_column(String, nullable=True)
    co            = mapped_column(String, nullable=True)
    requester     = mapped_column(String, nullable=True)
    phoneext      = mapped_column(Integer, nullable=True)
    datereq       = mapped_column(Date, nullable=True)
    dateneed      = mapped_column(Date, nullable=True)
    order_type    = mapped_column(String, nullable=True)
    status        = mapped_column(
        SQLEnum(
            ItemStatus,
            name="item_status",
            native_enum=False,
            values_callable=lambda enum: [e.value for e in enum]
        ),
        default=ItemStatus.NEW_REQUEST,
        nullable=False
    )
    created_time  = mapped_column(
        DateTime(timezone=True),
        default=utc_now_truncated,
        nullable=False
    )
    #---------------------------------------------------------------------
    # Relationships
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
    pr_line_items = relationship(
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
###################################################################################################
## Line Item Table
"""
Keeps track of the line items for the purchase request
"""
class PurchaseRequestLineItem(Base):
    __tablename__ = "pr_line_items"

    id                      = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid                    = mapped_column(String, unique=True, default=lambda: str(uuid.uuid4()))
    purchase_request_uuid   = mapped_column(String, ForeignKey("purchase_requests.uuid"), nullable=False, index=True)
    request_id              = mapped_column(String, ForeignKey("purchase_requests.request_id"), nullable=False, index=True)
    item_description        = mapped_column(Text,   nullable=False)
    justification           = mapped_column(Text,   nullable=False)
    train_not_aval          = mapped_column(Boolean, default=False, nullable=True)
    needs_not_meet          = mapped_column(Boolean, default=False, nullable=False)
    add_comments            = mapped_column(Text, nullable=True)
    budget_obj_code         = mapped_column(String, nullable=False)
    fund                    = mapped_column(String, nullable=False)
    quantity                = mapped_column(Integer,nullable=False)
    price_each              = mapped_column(Float,  nullable=False)
    total_price             = mapped_column(Float,  nullable=False)
    location                = mapped_column(String, nullable=False)
    is_cyber_sec_related    = mapped_column(Boolean, default=False, nullable=False)
    status                  = mapped_column(SQLEnum(ItemStatus, 
                                                    name="item_status",
                                                    native_enum=False,
                                                    values_callable=lambda enum: [e.value for e in enum]
                                                    ),
                                                    default=ItemStatus.NEW_REQUEST
                                                )
    created_time            = mapped_column(
                                 DateTime(timezone=True),
                                 default=utc_now_truncated,
                                 nullable=False
                             )

    #---------------------------------------------------------------------
    # ORM relationships
    purchase_request = relationship(
        "PurchaseRequest",
        back_populates="pr_line_items",
        foreign_keys=[purchase_request_uuid]
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

###################################################################################################
## approval TABLE
"""
FOR READ ONLY PURPOSES WHEN LOOKING AT THE APPROVALS
"""
class Approval(Base):
    __tablename__ =  "approvals"
    __searchable__ = ['id', 'uuid', 'irq1_id', 'co', 'requester', 'budget_obj_code', 'fund', 'train_not_aval', 'needs_not_meet',
                      'quantity', 'total_price', 'price_each', 'location', 'status', 'created_time']

    # Sequential id for user-facing operations
    id:                     Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid:                   Mapped[str] = mapped_column(String, unique=True, default=lambda: str(uuid.uuid4()))
    irq1_id:                Mapped[str] = mapped_column(String, nullable=True, unique=True)
    purchase_request_uuid:  Mapped[str] = mapped_column(String, ForeignKey("purchase_requests.uuid"), nullable=False, index=True)
    requester:              Mapped[str] = mapped_column(String, nullable=False)
    co:                     Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phoneext:               Mapped[int] = mapped_column(Integer, nullable=False)
    datereq:                Mapped[str] = mapped_column(String, nullable=False)      
    dateneed:               Mapped[Optional[str]] = mapped_column(String, nullable=True)      
    order_type:             Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_attachments:       Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    item_description:       Mapped[str] = mapped_column(Text, nullable=False)
    justification:          Mapped[str] = mapped_column(Text, nullable=False)
    train_not_aval:         Mapped[bool] = mapped_column(Boolean, nullable=True)
    needs_not_meet:         Mapped[bool] = mapped_column(Boolean, nullable=True)
    budget_obj_code:        Mapped[str] = mapped_column(String, nullable=False)
    fund:                   Mapped[str] = mapped_column(String, nullable=False)
    price_each:             Mapped[float] = mapped_column(Float, nullable=False)
    total_price:            Mapped[float] = mapped_column(Float, nullable=False)
    location:               Mapped[str] = mapped_column(String, nullable=False)
    quantity:               Mapped[int] = mapped_column(Integer, nullable=False)
    created_time:           Mapped[datetime] = mapped_column(DateTime, default=utc_now_truncated, nullable=False)
    is_cyber_sec_related:   Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
     
    status:                 Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus, 
                                                                name="item_status",
                                                                native_enum=False,
                                                                values_callable=lambda enum: [e.value for e in enum]
                                                                ),
                                                                default=ItemStatus.NEW_REQUEST
                                                            )
    # ———————————————————————————————————————————————————————————————————
    # RELATIONSHIPS
    # ———————————————————————————————————————————————————————————————————z
    # Join via the UUID field:
    purchase_request = relationship(
        "PurchaseRequest",
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
    @hybrid_property
    def request_id(self):
        return self.purchase_request.request_id

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

###################################################################################################
## Approval Event TABLE
"""
This is for incoming requests from an external system or webhook ("here's a JSON payload telling you to approve/deny").
"""
class TaskStatus(enum.Enum):
    NEW         = "NEW"
    PENDING     = "PENDING"
    PROCESSED   = "PROCESSED"
    ERROR       = "ERROR"
    CANCELLED   = "CANCELLED"
    
class PendingApproval(Base):
    __tablename__ = "pending_approvals"
    """
    This is more of a workflow table, it tracks the status of the approval process for a single line item.
    """

    task_id                    = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid                       = mapped_column(String, unique=True, default=lambda: str(uuid.uuid4()))
    purchase_request_uuid      = mapped_column(String, ForeignKey("purchase_requests.uuid"), nullable=False, index=True)
    pr_line_item_id           = mapped_column(Integer, ForeignKey("pr_line_items.id"), nullable=True, index=True)
    approval_uuid              = mapped_column(String, ForeignKey("approvals.uuid"), nullable=True, index=True)
    assigned_group             = mapped_column(String, nullable=False)

    # workflow‐status enum
    status                     = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.NEW,
        nullable=False
    )
    # What the approver decided
    action = mapped_column(
        SQLEnum(
            ItemStatus, 
            name="item_status",
            native_enum=False, 
            values_callable=lambda enum: [e.value for e in enum]
            ), 
        nullable=True)
    # Timestamps, error info, etc.
    created_at                 = mapped_column(
        DateTime(timezone=True),
        default=utc_now_truncated,
        nullable=False
    )
    processed_at               = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    error_message              = mapped_column(Text, nullable=True)

    # relationships
    purchase_request = relationship(
        "PurchaseRequest",
        back_populates="pending_approvals"
    )
    pr_line_item = relationship(
        "PurchaseRequestLineItem",
        back_populates="pending_approvals"
    )
    approval = relationship(
        "Approval",
        back_populates="pending_approvals"
    )

###################################################################################################
## Line Item Status TABLE ( This is the approval for a single line item, decision maker payload/table )
class LineItemApproval(Base):
    __tablename__ = "line_item_approvals"
    id            = mapped_column(Integer, primary_key=True)
    uuid          = mapped_column(String, unique=True, default=lambda: str(uuid.uuid4()))
    approvals_uuid = mapped_column(String, ForeignKey("approvals.uuid"), nullable=False, index=True)
    pr_line_item_uuid = mapped_column(String, ForeignKey("pr_line_items.uuid"), nullable=False, index=True)
    approver      = mapped_column(String, nullable=False)
    decision      = mapped_column(SQLEnum(ItemStatus), nullable=False)
    comments      = mapped_column(Text, nullable=True)
    created_at    = mapped_column(DateTime, default=utc_now_truncated, nullable=False)
    
    #---------------------------------------------------------------------
    # RELATIONSHIPS
    pr_line_items = relationship("PurchaseRequestLineItem", back_populates="line_item_approvals")
    approvals = relationship("Approval", back_populates="line_item_approvals")

###################################################################################################
## LINE ITEM COMMENTS TABLE
class SonComment(Base):
    __tablename__ = "son_comments"
    
    id:                 Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approvals_uuid:     Mapped[str] = mapped_column(String, ForeignKey("approvals.uuid"), nullable=False)
    request_id:			Mapped[str] = mapped_column(String, ForeignKey("purchase_requests.request_id"), nullable=False)
    comment_text:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:         Mapped[Optional[datetime]] = mapped_column(DateTime, default=utc_now_truncated, nullable=True)
    son_requester:      Mapped[str] = mapped_column(String, nullable=False)
    item_description:   Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    #---------------------------------------------------------------------
    # RELATIONSHIPS
    approvals = relationship(
        "Approval",
        foreign_keys=[approvals_uuid],
        back_populates="son_comments")

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
    return db_session.query(Approval).options(selectinload(Approval.purchase_request)).all()

def get_approval_by_id(db_session: Session, ID: str):
    return db_session.query(Approval).options(selectinload(Approval.purchase_request)).filter(Approval.request_id == ID).first()

###################################################################################################
# Get Purchase Request Header and Line Items
###################################################################################################
def get_pr_header_and_line_items(request_id: str):
    with get_session() as session:
        # 1) Load the header AND its .pr_line_items relationship in one query
        pr_header = session.scalar(
            select(PurchaseRequest)
            .options(selectinload(PurchaseRequest.pr_line_items))
            .where(PurchaseRequest.request_id == request_id)
        )
        if not pr_header:
            raise HTTPException(status_code=404, detail=f"Purchase Request '{request_id}' not found")

        # 2) The related items are now on pr_header.pr_line_items  
        line_items = pr_header.pr_line_items
        if not line_items:
            raise HTTPException(status_code=404, detail=f"No line items for Purchase Request '{request_id}'")

        return pr_header, line_items
    
###################################################################################################
# Get all son comments by id
###################################################################################################
def fetch_just_flags_by_id(id: str):
    with get_session() as session:
        stmt = (
            select(
                PurchaseRequestLineItem.train_not_aval,
                PurchaseRequestLineItem.needs_not_meet,
            ).join(
                PurchaseRequest,
                PurchaseRequest.uuid == PurchaseRequestLineItem.purchase_request_uuid
            ).where(
                PurchaseRequest.request_id == id
            )
        )
        results = session.execute(stmt).all()
        if not results:
            raise HTTPException(status_code=404, detail=f"No line items for Purchase Request '{id}'")
        return results
    
###################################################################################################
# Get all son comments by id
###################################################################################################
def get_all_son_comments(id: str):
    if not id:
        raise HTTPException(status_code=400, detail="id is required")
    with get_session() as session:
        stmt = select(SonComment).where(SonComment.purchase_request_id == id)
        son_comments = session.scalars(stmt).all()
        
        if not son_comments:
            raise HTTPException(status_code=404, detail="Son comment not found")
        
        return son_comments

###################################################################################################
# Get all add comments by id
###################################################################################################
def get_approval_by_id(id: str):
    
    with get_session() as session:
        stmt = (
			select(
				Approval.uuid,
				Approval.request_id,
			)
		)

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
    # return session.query(PurchaseRequest).all()
    pass

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