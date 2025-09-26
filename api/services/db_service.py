from __future__ import annotations
from api.settings import settings
from http.client import HTTPException
from api.schemas.approval_schemas import ApprovalSchema, ApprovalView
from api.schemas.ldap_schema import LDAPUser
from api.utils.misc_utils import format_username
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger
from aiocache import Cache, cached
from sqlalchemy import select, update, insert
from sqlalchemy import (create_engine, String, Integer, Float, Boolean, Text, LargeBinary, ForeignKey, DateTime,
                        Enum , JSON, func, Enum as SQLEnum, literal, func, select, text, UniqueConstraint)
from sqlalchemy.orm import declarative_base, selectinload, aliased
from sqlalchemy.orm import sessionmaker, relationship, Session
from api.schemas.boc_fund_mapping.boc_to_fund_mapping import BocMapping092000, BocMapping51140X, BocMapping51140E
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import select
from sqlalchemy.orm import aliased
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import List, Optional
from api.schemas.enums import AssignedGroup, ItemStatus
from api.utils.logging_utils import logger_init_ok
import uuid
import os
import sqlite3
import sys

# Ensure database directory exists
db_dir = os.path.join(os.path.dirname(__file__), '..', 'db')
os.makedirs(db_dir, exist_ok=True)

# Use absolute path for PyInstaller compatibility
if getattr(sys, 'frozen', False):
    # Running from PyInstaller executable
    base_path = os.path.dirname(sys.executable)
    db_path = os.path.join(base_path, 'db', 'pras.db')
    # Ensure the db directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
    print(f"DEBUG: PyInstaller mode - Database path: {db_path}")
    print(f"DEBUG: Base path: {base_path}")
    print(f"DEBUG: Database URL: {DATABASE_URL}")
else:
    # Running from source - use environment variable if set
    db_path = os.environ.get('DATABASE_FILE_PATH', 'api/db/pras.db')
    DATABASE_URL = f"sqlite:///{db_path}"
    print(f"DEBUG: Source mode - Database URL: {DATABASE_URL}")
    print(f"DEBUG: Database file path: {db_path}")

# Create engine and base
engine = create_engine(DATABASE_URL, echo=False)  # PRAS = Purchase Request Approval System
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# ────────────────────────────────────────────────────────────────────────────────
# ASYNC DATABASE ENGINE
# ────────────────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    # Running from PyInstaller executable
    base_path = os.path.dirname(sys.executable)
    db_path = os.path.join(base_path, 'db', 'pras.db')
    # Ensure the db directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    DATABASE_URL_ASYNC = f"sqlite+aiosqlite:///{db_path}"
    print(f"DEBUG: PyInstaller mode - Async Database path: {db_path}")
    print(f"DEBUG: Async Database URL: {DATABASE_URL_ASYNC}")
else:
    # Running from source - use environment variable if set
    db_path = os.environ.get('DATABASE_FILE_PATH', 'api/db/pras.db')
    DATABASE_URL_ASYNC = f"sqlite+aiosqlite:///{db_path}"
    print(f"DEBUG: Source mode - Async Database URL: {DATABASE_URL_ASYNC}")
    print(f"DEBUG: Async Database file path: {db_path}")
    
engine_async = create_async_engine(
    DATABASE_URL_ASYNC, 
    echo=False)

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
    purchase_request_seq_id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ID                     : Mapped[str] = mapped_column(String, unique=True, nullable=False)
    IRQ1_ID                : Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    CO                     : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    requester              : Mapped[str] = mapped_column(String, nullable=False)
    datereq                : Mapped[str] = mapped_column(String)
    orderType              : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pdf_output_path        : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contracting_officer_id : Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contracting_officers.id"), nullable=True)
    submission_status       : Mapped[str] = mapped_column(Enum("IN_PROGRESS", "SUBMITTED", "CANCELLED", name="submission_status_enum"),
                                                          nullable=False,
                                                          server_default="IN_PROGRESS")
    created_time = mapped_column(DateTime(timezone=True), default=utc_now_truncated, nullable=False)

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
    
    # headers -> contracting_officers
    contracting_officer : Mapped["ContractingOfficer"] = relationship(
        "ContractingOfficer",
        backref="purchase_request_header"
    )

# ────────────────────────────────────────────────────────────────────────────────
# PURCHASE REQUEST LINE ITEM
# ────────────────────────────────────────────────────────────────────────────────
class PurchaseRequestLineItem(Base):
    __tablename__ = "pr_line_items"

    UUID                   : Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_request_id    : Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.ID"), nullable=False)
    itemDescription        : Mapped[str] = mapped_column(Text)
    justification          : Mapped[str] = mapped_column(Text)
    addComments            : Mapped[Optional[str]] = mapped_column(Text)
    trainNotAval           : Mapped[bool] = mapped_column(Boolean, nullable=True)
    needsNotMeet           : Mapped[bool] = mapped_column(Boolean, nullable=True)
    budgetObjCode          : Mapped[str] = mapped_column(String)
    fund                   : Mapped[str] = mapped_column(String)
    quantity               : Mapped[int] = mapped_column(Integer)
    priceEach              : Mapped[float] = mapped_column(Float)
    originalTotalPrice     : Mapped[float] = mapped_column(Float)
    allowedIncreaseTotal   : Mapped[float] = mapped_column(Float, default=0.0)       
    priceUpdated           : Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    totalPrice             : Mapped[float] = mapped_column(Float)
    location               : Mapped[str] = mapped_column(String)
    isCyberSecRelated      : Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    uploaded_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

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
    final_approval_attr    : Mapped[List[FinalApproval]] = relationship(
                                "FinalApproval",
                                back_populates="line_item",
                                cascade="all, delete-orphan",
                                foreign_keys="[FinalApproval.line_item_uuid]"
                             )

    # line-item → pending approvals
    pending_approvals      : Mapped[List[PendingApproval]] = relationship(
                                "PendingApproval",
                                back_populates="purchase_request_line_item",
                                cascade="all, delete-orphan",
                                foreign_keys="[PendingApproval.line_item_uuid]"
                             )
    son_comments           : Mapped[List[SonComment]] = relationship(
                                "SonComment",
                                back_populates="line_item",
                                cascade="all, delete-orphan",
                                foreign_keys="[SonComment.line_item_uuid]"
                             )



# ────────────────────────────────────────────────────────────────────────────────
# APPROVAL (the master approval record) VIEW
# ────────────────────────────────────────────────────────────────────────────────
class Approval(Base):
    __tablename__ = "approvals"

    UUID                   : Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_request_id    : Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.ID"), nullable=False)
    IRQ1_ID                : Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    requester              : Mapped[str] = mapped_column(String, nullable=False)
    CO                     : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    datereq                : Mapped[str] = mapped_column(String)
    orderType              : Mapped[Optional[str]] = mapped_column(String, nullable=True)
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
    final_approval_attr    : Mapped[List[FinalApproval]] = relationship(
                                "FinalApproval",
                                back_populates="approval",
                                cascade="all, delete-orphan",
                                foreign_keys="[FinalApproval.approvals_uuid]"
                             )
    final_approval_by_pr_id: Mapped[List[FinalApproval]] = relationship(
                                "FinalApproval",
                                back_populates="approval_by_pr_id",
                                cascade="all, delete-orphan",
                                foreign_keys="[FinalApproval.purchase_request_id]"
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
# PENDING APPROVAL 
# ────────────────────────────────────────────────────────────────────────────────
"""
These approvals will be completed by the IT or Finance supervisors, then they will
go to FinalApproval where the Deputy Clerk or Clerk Admin will approve or deny the request.
"""
class PendingApproval(Base):
    __tablename__ = "pending_approvals"

    pending_approval_id    : Mapped[int]    = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_request_id    : Mapped[str]    = mapped_column(String, ForeignKey("purchase_request_headers.ID"), nullable=False)
    line_item_uuid         : Mapped[Optional[str]] = mapped_column(String, ForeignKey("pr_line_items.UUID"), nullable=True)
    approvals_uuid         : Mapped[Optional[str]] = mapped_column(String, ForeignKey("approvals.UUID"), nullable=True)
    assigned_group         : Mapped[str]    = mapped_column(String, nullable=False)
    
    status                 : Mapped[ItemStatus] = mapped_column(
                                SQLEnum(ItemStatus,
                                       name="item_status", native_enum=False,
                                       values_callable=lambda enum: [e.value for e in enum]
                                ),
                                default=ItemStatus.NEW_REQUEST
                              )
    
    final_approval_attr: Mapped[List[FinalApproval]] = relationship(
                                "FinalApproval",
                                back_populates="pending_approval",
                                cascade="all, delete-orphan",
                                foreign_keys="[FinalApproval.pending_approval_id]"
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

# ────────────────────────────────────────────────────────────────────────────────
# JOIN TABLE: FinalApproval
# ────────────────────────────────────────────────────────────────────────────────
class FinalApproval(Base):
    """
    The final say so on whether a request is approved or denied.
    """
    __tablename__ = "final_approvals"
    
    UUID            : Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_request_id : Mapped[str] = mapped_column(String, ForeignKey("approvals.purchase_request_id"), nullable=False)
    pending_approval_id         : Mapped[int] = mapped_column(Integer, ForeignKey("pending_approvals.pending_approval_id"), nullable=False)
    approvals_uuid  : Mapped[str] = mapped_column(String, ForeignKey("approvals.UUID"), nullable=False)
    line_item_uuid  : Mapped[str] = mapped_column(String, ForeignKey("pr_line_items.UUID"), nullable=False)
    status          = mapped_column(SQLEnum(ItemStatus), nullable=False)
    created_at      = mapped_column(DateTime, default=utc_now_truncated, nullable=False)
    deputy_can_approve = mapped_column(Boolean, nullable=False)  # total price must be equal to or less than $250
    pending_approved_by = mapped_column(String, nullable=True)
    pending_approved_at = mapped_column(DateTime, nullable=True)
    final_approved_by = mapped_column(String, nullable=True)
    final_approved_at = mapped_column(DateTime, nullable=True)

    # back to Approval
    approval        : Mapped[Approval] = relationship(
                          "Approval",
                          back_populates="final_approval_attr",
                          foreign_keys=[approvals_uuid]
                      )
    
    # back to Approval by purchase request id
    approval_by_pr_id : Mapped[Approval] = relationship(
							"Approval",
							back_populates="final_approval_by_pr_id",
							foreign_keys=[purchase_request_id]
						)

    # back to LineItem
    line_item      : Mapped[PurchaseRequestLineItem] = relationship(
                          "PurchaseRequestLineItem",
                          back_populates="final_approval_attr",
                          foreign_keys=[line_item_uuid]
                      )
    
    # back to PendingApproval
    pending_approval: Mapped[PendingApproval] = relationship(
                          "PendingApproval",
                          back_populates="final_approval_attr",
                          foreign_keys=[pending_approval_id]
                      )
    
# ────────────────────────────────────────────────────────────────────────────────
# SON COMMENT
# ────────────────────────────────────────────────────────────────────────────────
class SonComment(Base):
    __tablename__ = "son_comments"
    UUID:               Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    line_item_uuid:     Mapped[str] = mapped_column(String, ForeignKey("pr_line_items.UUID"), nullable=True)
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
    
    line_item: Mapped[PurchaseRequestLineItem] = relationship(
        "PurchaseRequestLineItem",
        back_populates="son_comments",
        foreign_keys=[line_item_uuid]
    )

# ────────────────────────────────────────────────────────────────────────────────
# Budget Funds
# ────────────────────────────────────────────────────────────────────────────────
class BudgetFund(Base):
    __tablename__ = "budget_fund"
    id:         Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code:  Mapped[str]  = mapped_column(String, unique=True, nullable=False, index=True)
    active:     Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))

    # one fund -> many BOCs
    bocs: Mapped[list["BudgetObjCode"]] = relationship(
        back_populates="fund",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

# ────────────────────────────────────────────────────────────────────────────────
# Budget Object Code
# ────────────────────────────────────────────────────────────────────────────────
class BudgetObjCode(Base):
    __tablename__ = "budget_object_code"
    id:        Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    boc_code:  Mapped[str]  = mapped_column(String, nullable=False, index=True)
    boc_name:  Mapped[str]  = mapped_column(String, nullable=False)
    active:    Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))

    # FK points to the FUND the BOC belongs to
    fund_code: Mapped[str]  = mapped_column(ForeignKey("budget_fund.fund_code"), nullable=False)
    
    # Composite unique constraint on boc_code + fund_code combination
    __table_args__ = (
        UniqueConstraint('boc_code', 'fund_code', name='uq_boc_fund'),
    )

    fund: Mapped["BudgetFund"] = relationship(back_populates="bocs")

# ────────────────────────────────────────────────────────────────────────────────
# CONTRACTING OFFICER
# ────────────────────────────────────────────────────────────────────────────────
class ContractingOfficer(Base):
    __tablename__ = "contracting_officers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
  
# ────────────────────────────────────────────────────────────────────────────────
# WORKFLOW USER
# ────────────────────────────────────────────────────────────────────────────────  
class WorkflowUser(Base):
    __tablename__ = "workflow_users"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    username = mapped_column(String, nullable=False)
    email = mapped_column(String, nullable=False, unique=False) # Unique if false FOR TESTING, simulate actual prod flow but just sending to roman_campbell
    department = mapped_column(String, nullable=False)
    active = mapped_column(Boolean, nullable=False, default=False)
    

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
    
# Create cache to store justification text
cache = Cache(Cache.MEMORY)

# Help function to fetch and cache justification text
@cached(ttl=300, cache=Cache.MEMORY, key="justification_templates")
async def get_justification_templates(db: AsyncSession) -> dict[str, str]:
    """
    Returns a dictionary mapping code -> template
    Cached in memory every 5minutes
    """
    result = await db.execute(select(JustificationTemplate))
    rows = result.scalars().all()
    return {r.code: r.description for r in rows}

###################################################################################################
# Get allowed increase total
###################################################################################################
async def get_allowed_increase_total(db: AsyncSession, purchase_request_id: str) -> float:
    stmt = select(PurchaseRequestLineItem.allowedIncreaseTotal).where(
        PurchaseRequestLineItem.purchase_request_id == purchase_request_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

###################################################################################################
# Set original total price
###################################################################################################
async def set_original_total_price(db: AsyncSession, purchase_request_id: str, original_total_price: float):
    stmt = update(PurchaseRequestLineItem).where(
        PurchaseRequestLineItem.purchase_request_id == purchase_request_id,
    ).values(originalTotalPrice=original_total_price).execution_options(synchronize_session="fetch")
    await db.execute(stmt)
    await db.commit()

###################################################################################################
# Set allowed increase total
###################################################################################################
async def set_allowed_increase_total(db: AsyncSession, purchase_request_id: str, allowed_increase_total: float):
    stmt = update(PurchaseRequestLineItem).where(
        PurchaseRequestLineItem.purchase_request_id == purchase_request_id
    ).values(allowedIncreaseTotal=allowed_increase_total).execution_options(synchronize_session="fetch")
    await db.execute(stmt)
    await db.commit()

###################################################################################################
# Get if price has been updated
###################################################################################################
async def get_has_price_updated(db: AsyncSession, purchase_request_id: str) -> bool:
    stmt = select(PurchaseRequestLineItem.priceUpdated).where(
        PurchaseRequestLineItem.purchase_request_id == purchase_request_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

###################################################################################################
# Get allowed increase total
###################################################################################################
async def get_allowed_increase_total(db: AsyncSession, purchase_request_id: str) -> float:
    stmt = select(PurchaseRequestLineItem.allowedIncreaseTotal).where(
        PurchaseRequestLineItem.purchase_request_id == purchase_request_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() or 0.0

###################################################################################################
# Get original total price
###################################################################################################
async def get_original_total_price(db: AsyncSession, purchase_request_id: str) -> float:
    stmt = select(PurchaseRequestLineItem.originalTotalPrice).where(
        PurchaseRequestLineItem.purchase_request_id == purchase_request_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() or 0.0

###################################################################################################
# Get line item quantity
###################################################################################################
async def get_line_item_quantity(db: AsyncSession, line_item_uuid: str) -> int:
    stmt = select(PurchaseRequestLineItem.quantity).where(
        PurchaseRequestLineItem.UUID == line_item_uuid
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

###################################################################################################
# Get next  request id
###################################################################################################
async def set_purchase_req_id(db: AsyncSession) -> str:
    new_req = PurchaseRequestHeader(
        ID="",
        requester="PENDING",
        datereq=utc_now_truncated().strftime("%Y-%m-%d"),
    )
    db.add(new_req)
    await db.flush()
    
    purchase_request_id = f"LAWB{new_req.purchase_request_seq_id:04d}"
    new_req.ID = purchase_request_id
    
    # Do not commit here, allow transaction to commit
    return purchase_request_id

###################################################################################################
# Get last row in purchase_request_headers
###################################################################################################
"""
Grab last row purchase request id and status, we only want to assign/do anything if the last row is IN_PROGRESS,
for assigning CO
"""
async def get_last_row_purchase_request_id(db: AsyncSession) -> tuple[str, str] | None:
    stmt = (select(
            PurchaseRequestHeader.submission_status,
            PurchaseRequestHeader.ID
        )
        .order_by(PurchaseRequestHeader.purchase_request_seq_id.desc())  # get the last row
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.first()

###################################################################################################
# Get last row in purchase_request_headers
###################################################################################################
async def get_last_row_submission_status(db: AsyncSession) -> str:
    stmt = (select(PurchaseRequestHeader.submission_status)
            .order_by(PurchaseRequestHeader.purchase_request_seq_id.desc())  # get the last row
            .limit(1)
            .where(PurchaseRequestHeader.submission_status == "SUBMITTED"))  # only get the last row that is submitted
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

###################################################################################################
# Check if there's already a pending/in-progress request
###################################################################################################
async def get_last_row_any_status(db: AsyncSession) -> str:
    stmt = (select(PurchaseRequestHeader.submission_status)
            .order_by(PurchaseRequestHeader.purchase_request_seq_id.desc())  # get the last row
            .limit(1))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

###################################################################################################
# Get all purchase requests
###################################################################################################
def get_all_purchase_requests(session):
    """Get all purchase requests"""
    return session.query(PurchaseRequestHeader).all()

###################################################################################################
# Get approval by purchase request ID -- FOR SEARCHING ON APPROVAL "VIEW"
###################################################################################################
def get_approval_by_id(session, purchase_request_id: str):
    """Get approval for a given purchase request ID"""
    return session.query(Approval).filter(Approval.purchase_request_id == purchase_request_id).first()

###################################################################################################
# Get justifications by ID
###################################################################################################
async def get_justifications_by_id(db: AsyncSession, ID: str) -> list[tuple[bool, bool]]:
    # These are the comments from justification, if trainNotAval or needsNotMeet is true, 
    # then we need to get the additional comments
    stmt = select(
        PurchaseRequestLineItem.trainNotAval,
        PurchaseRequestLineItem.needsNotMeet,
    ).where(
        PurchaseRequestLineItem.purchase_request_id == ID
    )
    result = await db.execute(stmt)
    rows = result.all()
    return rows

###################################################################################################
# Get son comments by ID
###################################################################################################
async def get_son_comments_by_id(
    db: AsyncSession,
    ID: str
) -> list[SonComment]:
    pass

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
    
    logger.debug(f"Fetching flat approvals for ID: {ID}")
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
            hdr.datereq.label("datereq"),
            hdr.orderType.label("orderType"),
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
# INSERT LINE ITEM FINAL APPROVAL
###################################################################################################
async def insert_final_approval(
    db: AsyncSession,
    approvals_uuid: str,
    purchase_request_id: str,
    line_item_uuid: str,
    pending_approval_id: int,
    status: ItemStatus,
    deputy_can_approve: bool = False,
    pending_approved_by: str = None,
    final_approved_by: str = None,
    pending_approved_at: datetime = None,
    final_approved_at: datetime = None,
) -> FinalApproval:
    """
    Insert a new record into the line_item_final_approvals table.
    
    Args:
        db: Database session
        approvals_uuid: UUID from the approvals table
        purchase_request_id: ID from the purchase_request_headers table
        line_item_uuid: UUID from the pr_line_items table
        pending_approval_id: Pending approval ID from the pending_approvals table
        approver: Username of the approver
        status: Current approval status
        deputy_can_approve: Whether deputy can approve (based on price <= $250)
    
    Returns:
        The created FinalApproval object
    """
    logger.info(f"Inserting line item final approval: {approvals_uuid}, {line_item_uuid}, {pending_approval_id}")

    # Create the new approval record
    final_approval = FinalApproval(
        approvals_uuid=approvals_uuid,
        purchase_request_id=purchase_request_id,
        line_item_uuid=line_item_uuid,
        pending_approval_id=pending_approval_id,
        status=status,
        deputy_can_approve=deputy_can_approve,
        pending_approved_by=format_username(pending_approved_by),
        pending_approved_at=pending_approved_at,
        final_approved_by=format_username(final_approved_by),
        final_approved_at=final_approved_at,
    )
    
    db.add(final_approval)
    await db.flush()
    await db.refresh(final_approval)
    await db.commit()  # Commit the transaction to persist the record
    
    logger.info(f"Successfully inserted line item final approval: {final_approval}")
    return final_approval

###################################################################################################
# GET LINE ITEM FINAL APPROVALS BY LINE ITEM UUID
###################################################################################################
async def get_final_approvals_by_line_item_uuid(
    db: AsyncSession,
    line_item_uuid: str
) -> List[FinalApproval]:
    """
    Get all final approval records for a specific line item.
    
    Args:
        db: Database session
        line_item_uuid: UUID of the line item
    
    Returns:
        List of FinalApproval objects
    """
    stmt = select(FinalApproval).where(
        FinalApproval.line_item_uuid == line_item_uuid
    )
    result = await db.execute(stmt)
    return result.scalars().all()


###################################################################################################
# GET LINE ITEM FINAL APPROVALS BY APPROVAL UUID
###################################################################################################
async def get_final_approvals_by_approval_uuid(
    db: AsyncSession,
    approvals_uuid: str
) -> List[FinalApproval]:
    """
    Get all final approval records for a specific approval.
    
    Args:
        db: Database session
        approvals_uuid: UUID of the approval
    
    Returns:
        List of FinalApproval objects
    """
    stmt = select(FinalApproval).where(
        FinalApproval.approvals_uuid == approvals_uuid
    )
    result = await db.execute(stmt)
    return result.scalars().all()

###################################################################################################
# UPDATE LINE ITEM FINAL APPROVAL STATUS
###################################################################################################
async def update_final_approval_status(
    db: AsyncSession,
    approvals_uuid: str,
    line_item_uuid: str,
    pending_approval_id: int,
    status: ItemStatus,
    final_approved_by: str,
    final_approved_at: datetime
) -> FinalApproval:
    """
    Update the status of a specific line item final approval.
    
    Args:
        db: Database session
        approvals_uuid: UUID from the approvals table
        line_item_uuid: UUID from the pr_line_items table
        pending_approval_id: Pending approval ID from the pending_approvals table
        new_status: New approval status
        approver: Username of the approver
    
    Returns:
        The updated FinalApproval object
    """
    logger.info(f"Updating line item final approval status: {approvals_uuid}, {line_item_uuid}, {pending_approval_id}")
    
    stmt = (
        update(FinalApproval)
        .where(
            FinalApproval.approvals_uuid == approvals_uuid,
            FinalApproval.line_item_uuid == line_item_uuid,
            FinalApproval.pending_approval_id == pending_approval_id
        )
        .values(
            status=status,
            final_approved_by=format_username(final_approved_by),
            final_approved_at=final_approved_at
        )
    )
    
    await db.execute(stmt)
    
    # Get the updated object
    result = await db.execute(
        select(FinalApproval).where(
            FinalApproval.approvals_uuid == approvals_uuid,
            FinalApproval.line_item_uuid == line_item_uuid,
            FinalApproval.pending_approval_id == pending_approval_id
        )
    )
    updated_obj = result.first()
    
    if not updated_obj:
        raise ValueError(f"Line item final approval not found: {approvals_uuid}, {line_item_uuid}, {pending_approval_id}")
    
    await db.commit()
    logger.info(f"Successfully updated line item final approval: {updated_obj}")
    return updated_obj

###################################################################################################
# DETERMINE DEPUTY APPROVAL ELIGIBILITY
###################################################################################################
def can_deputy_approve(total_price: float) -> bool:
    """
    Determine if a deputy can approve based on the total price.
    Deputies can approve requests with total price <= $250.
    
    Args:
        total_price: Total price of the line item
    
    Returns:
        True if deputy can approve, False otherwise
    """
    logger.debug(f"Total price: {total_price} can_deputy_approve function: {total_price <= 250.0}")
    return total_price <= 250.0

###################################################################################################
# GET ASSIGNED GROUP
###################################################################################################
async def get_assigned_group(db: AsyncSession, line_item_uuid: str) -> str:
    """Get the assigned group for a line item"""
    stmt = select(PendingApproval.assigned_group).where(PendingApproval.line_item_uuid == line_item_uuid)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

###################################################################################################
# CHECK FINAL APPROVAL STATUS
###################################################################################################
async def final_approval_check(
    db: AsyncSession, 
    line_item_uuid: str,
    LDAP_user: LDAPUser
):
    """Check the final approval status for a pending approval"""
    if LDAP_user.has_group("CUE"):
        stmt = select(
            FinalApproval.status,
            FinalApproval.deputy_can_approve
        ).where(
            FinalApproval.line_item_uuid == line_item_uuid
        )
        result = await db.execute(stmt)
        logger.info(f"Final approval check result: {result.scalar_one_or_none()}")
        return result.scalar_one_or_none()
        
    else:
        return False
    
###################################################################################################
# MARK FINAL APPROVAL AS APPROVED
###################################################################################################
async def mark_final_approval_as_approved(
    db: AsyncSession,
    approvals_uuid: str,
):
    await db.execute(
        update(FinalApproval)
        .where(FinalApproval.approvals_uuid == approvals_uuid)
        .values(status=ItemStatus.APPROVED)
    )
    await db.commit()
    
###################################################################################################
# GET FINAL APPROVED
###################################################################################################
async def get_final_approved_by_id(db: AsyncSession, ID: str) -> Optional[FinalApproval]:
    stmt = (
        select(FinalApproval.final_approved_by, FinalApproval.final_approved_at)
        .where(FinalApproval.purchase_request_id == ID)
    )
    result = await db.execute(stmt)
    rows = result.all()
    if not rows:
        logger.error(f"No final approved by ID: {ID}")
        return None
    
    # If multiple rows, use the first one (most recent)
    row = rows[0]
    return row.final_approved_by, row.final_approved_at
    
###################################################################################################
# GET CONTRACTING OFFICER BY ID
###################################################################################################
async def get_contracting_officer_by_id(db: AsyncSession, ID: str) -> str:
    """Get the contracting officer by LAWB ID"""
    try:
        stmt = select(Approval.CO).where(Approval.purchase_request_id == ID).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting contracting officer by ID: {e}")
        return None
		
###################################################################################################
# Initialize database
###################################################################################################
async def init_db():
    """Initialize the database by creating all tables."""
    #! ------------------------------------------------------------------------
    #! THIS IS PRODUCTION WORKFLOW USERS
    #! ------------------------------------------------------------------------
    # users = [
    #     WorkflowUser(username="lauren_lee", email="lauren_lee@lawb.uscourts.gov", department=AssignedGroup.FINANCE.value, active=True),
    #     WorkflowUser(username="peter_baltz", email="peter_baltz@lawb.uscourts.gov", department=AssignedGroup.FINANCE.value, active=False),
    #     WorkflowUser(username="lela_robichaux", email="lela_robichaux@lawb.uscourts.gov", department=AssignedGroup.MANAGEMENT.value, active=False),
    #     WorkflowUser(username="matthew_strong", email="matthew_strong@lawb.uscourts.gov", department=AssignedGroup.IT.value, active=False),
    #     WorkflowUser(username="roman_campbell", email="roman_campbell@lawb.uscourts.gov", department=AssignedGroup.IT.value, active=True),
    #     WorkflowUser(username="edmund_brown", email="edmund_brown@lawb.uscourts.gov", department=AssignedGroup.DEPUTY_CLERK.value, active=False),
    #     WorkflowUser(username="edward_takara", email="edward_takara@lawb.uscourts.gov", department=AssignedGroup.CHIEF_CLERK.value, active=False),
    # ]
    #! ------------------------------------------------------------------------
    #! THIS IS TESTING WORKFLOW USERS
    #! ------------------------------------------------------------------------
    users = [
        WorkflowUser(username="laurenlee", email="roman_campbell@lawb.uscourts.gov", department=AssignedGroup.FINANCE.value, active=True),
        WorkflowUser(username="peterbaltz", email="roman_campbell@lawb.uscourts.gov", department=AssignedGroup.FINANCE.value, active=True),
        WorkflowUser(username="lelarobichaux", email="roman_campbell@lawb.uscourts.gov", department=AssignedGroup.MANAGEMENT.value, active=True),
        WorkflowUser(username="matthewstrong", email="roman_campbell@lawb.uscourts.gov", department=AssignedGroup.IT.value, active=True),
        WorkflowUser(username="romancampbell", email="roman_campbell@lawb.uscourts.gov", department=AssignedGroup.IT.value, active=True),
        WorkflowUser(username="edmundbrown", email="roman_campbell@lawb.uscourts.gov", department=AssignedGroup.DEPUTY_CLERK.value, active=True),
        WorkflowUser(username="edwardtakara", email="roman_campbell@lawb.uscourts.gov", department=AssignedGroup.CHIEF_CLERK.value, active=True),
    ]

    try:
        # Create (sync) all tables
        Base.metadata.create_all(bind=engine)
        
        with sqlite3.connect(settings.DATABASE_FILE_PATH) as conn:
            cur = conn.cursor()
            with open(settings.SQL_SCRIPT_PATH, "r") as f:
                cur.executescript(f.read())
                
        logger_init_ok("SQL script executed successfully")
                
        # Seed workflow users
        async for session in get_async_session():
            try:
                # Check if any workflow users exist
                result = await session.execute(select(WorkflowUser).limit(1))
                existing_user = result.scalar_one_or_none()
                if not existing_user:
                    logger_init_ok("Seeding workflow users")
                    session.add_all(users)
                    await session.commit()
                break  # Exit the async generator after first iteration
            except Exception as e:
                logger.error(f"Error seeding workflow users: {e}")
                await session.rollback()
                break
        logger_init_ok("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    
    boc_mapping092000 = BocMapping092000()
    boc_mapping51140X = BocMapping51140X()
    boc_mapping51140E = BocMapping51140E()
    
    async for session in get_async_session():
        try:
            # Insert 092000 BOC mappings
            for boc_code, boc_name in boc_mapping092000.get_mapping_dict().items():
                # Use INSERT OR IGNORE to handle existing records
                await session.execute(
                    text("INSERT OR IGNORE INTO budget_object_code (boc_code, boc_name, fund_code) VALUES (:boc_code, :boc_name, :fund_code)"),
                    {"boc_code": boc_code, "boc_name": boc_name, "fund_code": "092000"}
                )
            
            # Insert 51140X BOC mappings
            for boc_code, boc_name in boc_mapping51140X.get_mapping_dict().items():
                await session.execute(
                    text("INSERT OR IGNORE INTO budget_object_code (boc_code, boc_name, fund_code) VALUES (:boc_code, :boc_name, :fund_code)"),
                    {"boc_code": boc_code, "boc_name": boc_name, "fund_code": "51140X"}
                )
            
            # Insert 51140E BOC mappings
            for boc_code, boc_name in boc_mapping51140E.get_mapping_dict().items():
                await session.execute(
                    text("INSERT OR IGNORE INTO budget_object_code (boc_code, boc_name, fund_code) VALUES (:boc_code, :boc_name, :fund_code)"),
                    {"boc_code": boc_code, "boc_name": boc_name, "fund_code": "51140E"}
                )
                
            await session.commit()
            logger_init_ok("BOC mappings inserted successfully")
        except Exception as e:
            logger.error(f"Error inserting BOC mappings: {e}")
            await session.rollback()
        finally:
            await session.close()

###################################################################################################
# DEBUG: CHECK WORKFLOW USER STATUS
###################################################################################################
async def debug_check_workflow_user(db_session: AsyncSession, username: str) -> Optional[dict]:
    """Debug function to check workflow user status"""
    stmt = select(WorkflowUser.username, WorkflowUser.active, WorkflowUser.department).where(
        WorkflowUser.username == username
    )
    result = await db_session.execute(stmt)
    row = result.first()
    
    if row:
        return {
            "username": row.username,
            "active": row.active,
            "department": row.department
        }
    return None

###################################################################################################
# GET UUID BY ID (UNCACHED)
###################################################################################################
async def get_uuid_by_id(db_session: AsyncSession, ID: str) -> Optional[str]:
    """
    This works with IDs so users will have the ability to take actions
    on individual line items.
    """
    stmt = select(PurchaseRequestLineItem.UUID).where(PurchaseRequestLineItem.purchase_request_id == ID)
    result = await db_session.execute(stmt)
    uuid_row = result.first()
    return uuid_row[0] if uuid_row else None

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
# RESET REQUEST TO NEW REQUEST
###################################################################################################
async def reset_purchase_request(purchase_request_id: str, db: AsyncSession):
    stmt = (
		update(PurchaseRequestHeader)
	)
    
###################################################################################################
# GET APPROVAL ROW COUNT
###################################################################################################
async def get_approval_row_count(purchase_request_id: str, db: AsyncSession) -> int:
    stmt = select(func.count(PendingApproval.purchase_request_id)).where(PendingApproval.purchase_request_id == purchase_request_id)
    result = await db.execute(stmt)
    return result.scalar_one()