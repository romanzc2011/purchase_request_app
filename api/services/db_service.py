from __future__ import annotations
from datetime import datetime, timezone
from http.client import HTTPException
from api.schemas.approval_schemas import ApprovalSchema, ApprovalView
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger
from aiocache import Cache, cached
from sqlalchemy import select
from sqlalchemy import (create_engine, String, Integer, Float, Boolean, Text, LargeBinary, ForeignKey, DateTime,
                        Enum as SAEnum, JSON, func, Enum as SQLEnum, literal, func, select, text)
from sqlalchemy.orm import declarative_base, selectinload, aliased
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.inspection import inspect
from sqlalchemy import select
from sqlalchemy.orm import aliased
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import List, Optional
from api.schemas.enums import ItemStatus, TaskStatus
import uuid
import os
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

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

# ────────────────────────────────────────────────────────────────────────────────
# DATABASE SESSIONS
# ────────────────────────────────────────────────────────────────────────────────
# Context manager for database sessions
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

# ────────────────────────────────────────────────────────────────────────────────
# PURCHASE REQUEST HEADER
# ────────────────────────────────────────────────────────────────────────────────
class PurchaseRequestHeader(Base):
    __tablename__ = "purchase_request_headers"

    ID                 : Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    IRQ1_ID      	   : Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    CO           	   : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    requester          : Mapped[str] = mapped_column(String, nullable=False)
    phoneext           : Mapped[int] = mapped_column(Integer, nullable=False)
    datereq            : Mapped[str] = mapped_column(String)
    dateneed           : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    orderType          : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_time       = mapped_column(DateTime(timezone=True), default=utc_now_truncated, nullable=False)

    # 1️⃣ headers → line‐items
    pr_line_items      : Mapped[List[PurchaseRequestLineItem]] = relationship(
                            "PurchaseRequestLineItem",
                            back_populates="purchase_request_header",
                            cascade="all, delete-orphan",
                            foreign_keys="[PurchaseRequestLineItem.purchase_request_id]"
                         )

    # 2️⃣ headers → approvals
    approvals          : Mapped[List[Approval]] = relationship(
                            "Approval",
                            back_populates="purchase_request_header",
                            cascade="all, delete-orphan",
                            foreign_keys="[Approval.purchase_request_id]"
                         )

    # 3️⃣ headers → pending approvals
    pending_approvals  : Mapped[List[PendingApproval]] = relationship(
                            "PendingApproval",
                            back_populates="purchase_request_header",
                            cascade="all, delete-orphan",
                            foreign_keys="[PendingApproval.purchase_request_id]"
                         )


# ────────────────────────────────────────────────────────────────────────────────
# PURCHASE REQUEST LINE ITEM
# ────────────────────────────────────────────────────────────────────────────────

class PurchaseRequestLineItem(Base):
    __tablename__ = "pr_line_items"

    UUID                   : Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_request_id  : Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.ID"), nullable=False)
    itemDescription        : Mapped[str] = mapped_column(Text)
    justification          : Mapped[str] = mapped_column(Text)
    addComments            : Mapped[Optional[str]] = mapped_column(Text)
    trainNotAval           : Mapped[bool] = mapped_column(Boolean, nullable=True)
    needsNotMeet           : Mapped[bool] = mapped_column(Boolean, nullable=True)
    budgetObjCode          : Mapped[str] = mapped_column(String)
    fund                   : Mapped[str] = mapped_column(String)
    quantity               : Mapped[int] = mapped_column(Integer)
    priceEach              : Mapped[float] = mapped_column(Float)
    totalPrice             : Mapped[float] = mapped_column(Float)
    location               : Mapped[str] = mapped_column(String)
    isCyberSecRelated	   : Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)

    status                 : Mapped[ItemStatus] = mapped_column(
                                SQLEnum(ItemStatus,
                                       name="item_status", native_enum=False,
                                       values_callable=lambda enum: [e.value for e in enum]
                                ),
                                default=ItemStatus.NEW_REQUEST
                              )
    created_time           : Mapped[datetime] = mapped_column(DateTime, default=utc_now_truncated, nullable=False)

    # back to header
    purchase_request_header: Mapped[PurchaseRequestHeader] = relationship(
                                "PurchaseRequestHeader",
                                back_populates="pr_line_items",
                                foreign_keys=[purchase_request_id]
                             )

    # line-item → join‐table
    line_item_approval_attr    : Mapped[List[LineItemApproval]] = relationship(
                                "LineItemApproval",
                                back_populates="line_item",
                                cascade="all, delete-orphan",
                                foreign_keys="[LineItemApproval.line_item_uuid]"
                             )

    # line-item → pending approvals
    pending_approvals      : Mapped[List[PendingApproval]] = relationship(
                                "PendingApproval",
                                back_populates="purchase_request_line_item",
                                cascade="all, delete-orphan",
                                foreign_keys="[PendingApproval.line_item_uuid]"
                             )
    
class SonComment(Base):
    __tablename__ = "son_comments"
    UUID:               Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    approvals_uuid:     Mapped[str] = mapped_column(String, ForeignKey("approvals.UUID"), nullable=True)
    comment_text:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:         Mapped[Optional[datetime]] = mapped_column(DateTime, default=utc_now_truncated, nullable=True)
    son_requester:      Mapped[str] = mapped_column(String, nullable=False)
    item_description:   Mapped[Optional[str]] = mapped_column(String, nullable=True)	

    approval: Mapped[Approval] = relationship(
        "Approval",
        back_populates="son_comments",
        foreign_keys=[approvals_uuid]
    )


# ────────────────────────────────────────────────────────────────────────────────
# APPROVAL (the master approval record) VIEW
# ────────────────────────────────────────────────────────────────────────────────

class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = {'info': {'read_only': True}}

    UUID                   : Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_request_id    : Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.ID"), nullable=False)
    IRQ1_ID                : Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    requester              : Mapped[str] = mapped_column(String, nullable=False)
    CO                     : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phoneext               : Mapped[int] = mapped_column(Integer, nullable=False)
    datereq                : Mapped[str] = mapped_column(String)
    dateneed               : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    orderType              : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fileAttachments        : Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    itemDescription        : Mapped[str] = mapped_column(Text)
    justification          : Mapped[str] = mapped_column(Text)
    trainNotAval           : Mapped[bool] = mapped_column(Boolean, nullable=True)
    needsNotMeet           : Mapped[bool] = mapped_column(Boolean, nullable=True)
    budgetObjCode          : Mapped[str] = mapped_column(String)
    fund                   : Mapped[str] = mapped_column(String)
    priceEach              : Mapped[float] = mapped_column(Float)
    totalPrice             : Mapped[float] = mapped_column(Float)
    location               : Mapped[str] = mapped_column(String)
    quantity               : Mapped[int] = mapped_column(Integer)
    created_time           : Mapped[datetime] = mapped_column(DateTime, default=utc_now_truncated, nullable=False)
    isCyberSecRelated      : Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    status                 : Mapped[ItemStatus] = mapped_column(
                                SQLEnum(ItemStatus,
                                       name="item_status", native_enum=False,
                                       values_callable=lambda enum: [e.value for e in enum]
                                ),
                                default=ItemStatus.NEW_REQUEST
                              )

    # back to header
    purchase_request_header: Mapped[PurchaseRequestHeader] = relationship(
                                "PurchaseRequestHeader",
                                back_populates="approvals",
                                foreign_keys=[purchase_request_id]
                             )

    # to join‐table
    line_item_approval_attr    : Mapped[List[LineItemApproval]] = relationship(
                                "LineItemApproval",
                                back_populates="approval",
                                cascade="all, delete-orphan",
                                foreign_keys="[LineItemApproval.approvals_uuid]"
                             )

    # to pending
    pending_approvals      : Mapped[List[PendingApproval]] = relationship(
                                "PendingApproval",
                                back_populates="approval",
                                cascade="all, delete-orphan",
                                foreign_keys="[PendingApproval.approvals_uuid]"
                             )

    # to SonComment
    son_comments           : Mapped[List[SonComment]] = relationship(
                                "SonComment",
                                back_populates="approval",
                                cascade="all, delete-orphan",
                                foreign_keys="[SonComment.approvals_uuid]"
                             )


# ────────────────────────────────────────────────────────────────────────────────
# JOIN TABLE: LineItemApproval
# ────────────────────────────────────────────────────────────────────────────────

class LineItemApproval(Base):
    __tablename__ = "line_item_approvals"

    approvals_uuid  : Mapped[str] = mapped_column(String, ForeignKey("approvals.UUID"), primary_key=True)
    line_item_uuid  : Mapped[str] = mapped_column(String, ForeignKey("pr_line_items.UUID"), primary_key=True)
    approver        = mapped_column(String, nullable=False)
    status          = mapped_column(SQLEnum(ItemStatus), nullable=False)
    decision        = mapped_column(SQLEnum(ItemStatus), nullable=False)
    created_at      = mapped_column(DateTime, default=utc_now_truncated, nullable=False)

    # back to Approval
    approval        : Mapped[Approval] = relationship(
                          "Approval",
                          back_populates="line_item_approval_attr",
                          foreign_keys=[approvals_uuid]
                      )

    # back to LineItem
    line_item      : Mapped[PurchaseRequestLineItem] = relationship(
                          "PurchaseRequestLineItem",
                          back_populates="line_item_approval_attr",
                          foreign_keys=[line_item_uuid]
                      )


# ────────────────────────────────────────────────────────────────────────────────
# PENDING APPROVAL
# ────────────────────────────────────────────────────────────────────────────────

class PendingApproval(Base):
    __tablename__ = "pending_approvals"

    task_id                : Mapped[int]    = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_request_id    : Mapped[str]    = mapped_column(String, ForeignKey("purchase_request_headers.ID"), nullable=False)
    line_item_uuid         : Mapped[Optional[str]] = mapped_column(String, ForeignKey("pr_line_items.UUID"), nullable=True)
    approvals_uuid         : Mapped[Optional[str]] = mapped_column(String, ForeignKey("approvals.UUID"), nullable=True)
    assigned_group         : Mapped[str]    = mapped_column(String, nullable=False)
    task_status            : Mapped[TaskStatus] = mapped_column(
                                SQLEnum(TaskStatus),
                                name="task_status", native_enum=False,
                                values_callable=lambda enum: [e.value for e in enum],
                                default=TaskStatus.NEW_REQUEST,
                                nullable=False
                             )
    action                 = mapped_column(
                                SQLEnum(ItemStatus, name="item_status", native_enum=False,
                                       values_callable=lambda enum: [e.value for e in enum]
                                ),
                                nullable=True
                             )
    created_at             = mapped_column(DateTime(timezone=True), default=utc_now_truncated, nullable=False)
    processed_at           = mapped_column(DateTime(timezone=True), default=utc_now_truncated, nullable=True)

    # back to header
    purchase_request_header: Mapped[PurchaseRequestHeader] = relationship(
                                "PurchaseRequestHeader",
                                back_populates="pending_approvals",
                                foreign_keys=[purchase_request_id]
                             )

    # back to line‐item
    purchase_request_line_item: Mapped[PurchaseRequestLineItem] = relationship(
                                "PurchaseRequestLineItem",
                                back_populates="pending_approvals",
                                foreign_keys=[line_item_uuid]
                             )

    # back to approval
    approval                : Mapped[Approval] = relationship(
                                "Approval",
                                back_populates="pending_approvals",
                                foreign_keys=[approvals_uuid]
                             )
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

def get_approval_by_id(session, ID):
    return session.query(Approval).filter(Approval.purchase_request_id == ID).first()

###################################################################################################
# Get Purchase Request Header and Line Items
###################################################################################################
def get_pr_header_and_line_items(request_id: str):
    with get_session() as session:
        # 1) Load the header AND its .pr_line_items relationship in one query
        pr_header = session.scalar(
            select(PurchaseRequestHeader)
            .options(selectinload(PurchaseRequestHeader.pr_line_item_attr))
            .where(PurchaseRequestHeader.request_id == request_id)
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
                PurchaseRequestLineItem.trainNotAval,
                PurchaseRequestLineItem.needsNotMeet,
            ).join(
                PurchaseRequestHeader,
                PurchaseRequestHeader.ID == PurchaseRequestLineItem.purchase_request_id
            ).where(
                PurchaseRequestHeader.ID == id
            )
        )
        results = session.execute(stmt).all()
        if not results:
            raise HTTPException(status_code=404, detail=f"No line items for Purchase Request '{id}'")
        return results

###################################################################################################
# Get next  request id
###################################################################################################
def set_purchase_req_id() -> str:
    first_prefix = "LAWB"
    try:
        with get_session() as session:
            # Get all existing IDs and find the highest numeric suffix
            existing_ids = session.query(PurchaseRequestHeader.ID).all()
            max_suffix = 0
            
            for (id_str,) in existing_ids:
                if id_str and id_str.startswith(first_prefix):
                    try:
                        suffix = int(id_str[len(first_prefix):])
                        max_suffix = max(max_suffix, suffix)
                    except ValueError:
                        continue
            
            next_suffix = max_suffix + 1
            next_id = f"{first_prefix}{str(next_suffix).zfill(4)}"
            logger.info(f"Next purchase request id: {next_id}")
            return next_id
    except Exception as e:
        logger.error(f"Error setting purchase request id: {e}")
        # Return a fallback ID instead of None
        return f"{first_prefix}0001"

###################################################################################################
# Get status of request from Approval table
###################################################################################################
def get_status_by_id(db_session: Session, ID: str):
    logger.info(f"Fetching status for ID: {ID}")
    
    if not ID:
        raise ValueError("ID must be a non-empty string")
    
    # First try to find by sequential ID
    result = db_session.query(Approval).filter(Approval.purchase_request_id == ID).first()
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
        
    # Strip out keys that are not in model
    valid_cols = set(inspect(model).columns.keys())
    filtered_data = {k: v for k, v in kwargs.items() if k in valid_cols}
    
    with get_session() as session:
        # Filters incoming data by UUID for the table
        #Line Item Statuses needs to use approve_uuid 
        obj = session.query(model).filter(getattr(model, pk_field) == uuid).first()
        if not obj:
            raise ValueError(f"Object with UUID {uuid} not found in {table}")
        
        # Update the object with the filtered data
        for key, value in filtered_data.items():
            setattr(obj, key, value)
        
        session.commit()
        session.refresh(obj)
        logger.info(f"Updated data in {table}")
        return obj

###################################################################################################
# GET UUID BY ID (CACHED)
###################################################################################################
def get_uuid_by_id_cached(db_session: Session, ID: str):
    """
    Get UUID by ID with caching for performance.
    Returns the UUID if found, None otherwise.
    """
    # Check cache first
    if ID in _uuid_cache:
        logger.info(f"Cache hit for ID: {ID}")
        return _uuid_cache[ID]
    
    # Query database
    result = db_session.query(Approval.UUID).filter(Approval.purchase_request_id == ID).first()
    
    if result:
        uuid_value = result[0]
        # Cache the result
        _uuid_cache[ID] = uuid_value
        logger.info(f"Cache miss for ID: {ID}, cached UUID: {uuid_value}")
        return uuid_value
    else:
        logger.warning(f"No UUID found for ID: {ID}")
        return None

###################################################################################################
# GET UUID BY ID (UNCACHED)
###################################################################################################
def get_uuid_by_id(db_session: Session, ID: str):
    """
    Get UUID by ID without caching.
    Returns the UUID if found, None otherwise.
    """
    result = db_session.query(Approval.UUID).filter(Approval.purchase_request_id == ID).first()
    return result[0] if result else None

###################################################################################################
# FETCH SINGLE ROW
###################################################################################################
def fetch_single_row(self, model_class, columns: list, condition, params: dict):
    """
    Fetch a single row from the database.
    Returns the first row that matches the condition, or None if no match.
    """
    if not columns:
        raise ValueError("Columns must be a non-empty list")
    
    with get_session() as session:
        result = session.query(*columns).filter(condition).params(params).first()
        return result

###################################################################################################
# Get status of request from Approval table by uuid
###################################################################################################
def get_status_by_uuid(db_session: Session, UUID: str):
    logger.info(f"Fetching status for UUID: {UUID}")
    
    if not UUID:
        raise ValueError("UUID must be a non-empty string")
    
    # Query the Approval table to get the status field for the given uuid
    result = db_session.query(Approval.status).filter(Approval.UUID == UUID).first()
    logger.info(f"Status: {result}")
    
    if result:
        return result[0]  # Return just the status string
    else:
        logger.error(f"Object with UUID {UUID} not found in Approval table")
        raise ValueError(f"Object with UUID {UUID} not found in Approval table")

###################################################################################################
# GET UUIDS BY IDS
###################################################################################################
def get_uuids_by_ids(db_session: Session, IDs: list):
    """
    Get UUIDs for a list of IDs.
    Returns a dictionary mapping ID -> UUID.
    """
    if not IDs:
        return {}
    
    results = db_session.query(Approval.purchase_request_id, Approval.UUID).filter(Approval.purchase_request_id.in_(IDs)).all()
    return {row[0]: row[1] for row in results}

###################################################################################################
# GET USERNAMES
###################################################################################################
def get_usernames(db_session: Session, prefix: str):
    """
    Get usernames that start with the given prefix.
    Returns a list of usernames.
    """
    results = db_session.query(Approval.requester).filter(Approval.requester.like(f"{prefix}%")).distinct().all()
    return [row[0] for row in results]

###################################################################################################
# CHECK STATUS VALUES
###################################################################################################
def check_status_values():
    """Check what status values exist in the database"""
    with get_session() as session:
        # Check approvals table
        approval_statuses = session.query(Approval.status).distinct().all()
        logger.info(f"Approval statuses: {[s[0] for s in approval_statuses]}")
        
        # Check purchase request headers table
        header_statuses = session.query(PurchaseRequestHeader.status).distinct().all()
        logger.info(f"Header statuses: {[s[0] for s in header_statuses]}")
        
        # Check line items table
        line_item_statuses = session.query(PurchaseRequestLineItem.status).distinct().all()
        logger.info(f"Line item statuses: {[s[0] for s in line_item_statuses]}")
        
        return {
            "approvals": [s[0] for s in approval_statuses],
            "headers": [s[0] for s in header_statuses],
            "line_items": [s[0] for s in line_item_statuses]
        }

###################################################################################################
# Get all son comments by id
###################################################################################################
def get_all_son_comments(db_session: Session, id: str):
    """Get all son comments for a given ID"""
    results = db_session.query(SonComment).filter(SonComment.purchase_req_id == id).all()
    return results

###################################################################################################
# Get all purchase requests
###################################################################################################
def get_all_purchase_requests(session):
    """Get all purchase requests"""
    return session.query(PurchaseRequestHeader).all()

###################################################################################################
# Get additional comments by ID
###################################################################################################
def get_additional_comments_by_id(ID: str):
    """Get additional comments by ID"""
    with get_session() as session:
        stmt = (
            select(PurchaseRequestLineItem.addComments)
            .join(
                PurchaseRequestHeader,
                PurchaseRequestHeader.ID == PurchaseRequestLineItem.purchase_request_id
            ).where(
                PurchaseRequestHeader.ID == ID
            )
        )
        results = session.execute(stmt).all()
        return [row[0] for row in results if row[0]]

###################################################################################################
# Get order types by ID
###################################################################################################
def get_order_types(ID: str):
    """Get order types by ID"""
    with get_session() as session:
        stmt = (
            select(PurchaseRequestHeader.orderType)
            .where(PurchaseRequestHeader.ID == ID)
        )
        results = session.execute(stmt).all()
        return [row[0] for row in results if row[0]]

###################################################################################################
# Get next request ID
###################################################################################################
async def get_next_request_id() -> str:
    """
    Build the next ID in "YYYYMMDD-XXXX" format:
    - If today's date ≠ last ID's date, start at 0001
    - Otherwise increment the last 4‑digit suffix
    """
    first_section = "LAWB"
    async with get_session() as session:
        result = await session.execute(
            select(PurchaseRequestHeader.ID)
            .order_by(PurchaseRequestHeader.ID.desc())
            .limit(1)
        )
        last_id = result.scalar_one_or_none()
    
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

# ────────────────────────────────────────────────────────────────────────────────
# ORM Approval Flattening to match previous approval view
# This has become required because of the substantial backend refactoring
# and database normalization. This way we can view the Approval table without issue
# ────────────────────────────────────────────────────────────────────────────────
ORM_Approval = (
	PurchaseRequestHeader,
	PurchaseRequestLineItem,
	Approval
)

async def fetch_flat_approvals(
	db: AsyncSession,
	ID: Optional[str] = None,
) -> List[ApprovalSchema]:
    
    # alias each table for clarity
    hdr = aliased(PurchaseRequestHeader)
    li = aliased(PurchaseRequestLineItem)
    
    # build the statement to match ApprovalSchema structure
    stmt = (
        select(
            # ApprovalSchema fields
            li.UUID.label("UUID"),
            hdr.ID.label("purchase_request_id"),  # This will be aliased to "ID"
            hdr.IRQ1_ID.label("IRQ1_ID"),
            hdr.requester.label("requester"),
            hdr.CO.label("CO"),
            hdr.phoneext.label("phoneext"),
            hdr.datereq.label("datereq"),
            hdr.dateneed.label("dateneed"),
            hdr.orderType.label("orderType"),
            literal(None).label("fileAttachments"),  # Set to None for now
            li.itemDescription.label("itemDescription"),
            li.justification.label("justification"),
            li.trainNotAval.label("trainNotAval"),
            li.needsNotMeet.label("needsNotMeet"),
            li.budgetObjCode.label("budgetObjCode"),
            li.fund.label("fund"),
            li.priceEach.label("priceEach"),
            li.totalPrice.label("totalPrice"),
            li.location.label("location"),
            li.quantity.label("quantity"),
            li.created_time.label("created_time"),  # This will be aliased to "createdTime"
            li.isCyberSecRelated.label("isCyberSecRelated"),
            li.status.label("status"),
        )
        .select_from(li)
        .join(hdr, li.purchase_request_id == hdr.ID)
    )

    if ID:
        stmt = stmt.where(hdr.ID == ID)
    
    # execute the statement
    result = await db.execute(stmt)
    rows = result.all()
    
    # Map each row to the ApprovalSchema
    return [ApprovalSchema(**r._asdict()) for r in rows]

###################################################################################################
# Initialize database
###################################################################################################
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

init_db()