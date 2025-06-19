from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

# Create base class for declarative models
Base = declarative_base()

# Helper function to get UTC time
def utc_now_truncated() -> datetime:
    return datetime.now().replace(microsecond=0)

class PurchaseRequestHeader(Base):
    __tablename__ = "purchase_request_headers"
    
    # Primary key
    UUID: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Fields
    ID: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    requester: Mapped[str] = mapped_column(String, nullable=False)
    phoneext: Mapped[str] = mapped_column(String)
    datereq: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dateneed: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    orderType: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now_truncated)
    
    # Relationships
    line_items: Mapped[list["PurchaseRequestLineItem"]] = relationship("PurchaseRequestLineItem", back_populates="header", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="header", cascade="all, delete-orphan")

class PurchaseRequestLineItem(Base):
    __tablename__ = "pr_line_items"
    
    # Primary key
    UUID: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    purchase_request: Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.UUID"), nullable=False)
    
    # Fields
    ID: Mapped[str] = mapped_column(String, nullable=False)
    itemDescription: Mapped[str] = mapped_column(Text)
    justification: Mapped[str] = mapped_column(Text)
    addComments: Mapped[str] = mapped_column(Text)
    trainNotAval: Mapped[bool] = mapped_column(Boolean, default=False)
    needsNotMeet: Mapped[bool] = mapped_column(Boolean, default=False)
    budgetObjCode: Mapped[str] = mapped_column(String)
    fund: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    priceEach: Mapped[float] = mapped_column(Float)
    totalPrice: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    fileAttachments: Mapped[str] = mapped_column(Text)
    isCyberSecRelated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now_truncated)
    
    # Relationships
    header: Mapped["PurchaseRequestHeader"] = relationship("PurchaseRequestHeader", back_populates="line_items")

class Approval(Base):
    __tablename__ = "approvals"
    
    # Primary key
    UUID: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    purchase_request_uuid: Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.UUID"), nullable=False)
    
    # Fields
    requester: Mapped[str] = mapped_column(String, nullable=False)
    phoneext: Mapped[str] = mapped_column(String)
    datereq: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dateneed: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    orderType: Mapped[str] = mapped_column(String, nullable=False)
    itemDescription: Mapped[str] = mapped_column(Text)
    justification: Mapped[str] = mapped_column(Text)
    trainNotAval: Mapped[bool] = mapped_column(Boolean, default=False)
    needsNotMeet: Mapped[bool] = mapped_column(Boolean, default=False)
    budgetObjCode: Mapped[str] = mapped_column(String)
    fund: Mapped[str] = mapped_column(String)
    priceEach: Mapped[float] = mapped_column(Float)
    totalPrice: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    isCyberSecRelated: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String)
    created_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now_truncated)
    
    # Relationships
    header: Mapped["PurchaseRequestHeader"] = relationship("PurchaseRequestHeader", back_populates="approvals")

class PendingApproval(Base):
    __tablename__ = "pending_approvals"
    
    # Primary key
    UUID: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    purchase_request_uuid: Mapped[str] = mapped_column(String, ForeignKey("purchase_request_headers.UUID"), nullable=False)
    
    # Fields
    approver: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now_truncated)
    
    # Relationships
    header: Mapped["PurchaseRequestHeader"] = relationship("PurchaseRequestHeader")

class LineItemApproval(Base):
    __tablename__ = "line_item_approvals"
    # Composite primary key
    approvals_uuid: Mapped[str] = mapped_column(String, ForeignKey("approvals.UUID"), primary_key=True)
    line_item_uuid: Mapped[str] = mapped_column(String, ForeignKey("pr_line_items.UUID"), primary_key=True)
    approver: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_truncated, nullable=False)

    # Relationships
    approval_attr = relationship(
        "Approval",
        back_populates="line_item_approval_attr",
        foreign_keys=[approvals_uuid]
    )
    pr_line_item_attr = relationship(
        "PurchaseRequestLineItem",
        back_populates="line_item_approval_attr",
        foreign_keys=[line_item_uuid]
    )

class SonComment(Base):
    __tablename__ = "son_comments"
    approvals_uuid: Mapped[str] = mapped_column(String, ForeignKey("approvals.UUID"), primary_key=True, nullable=False)
    comment_text: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_truncated, nullable=True)
    son_requester: Mapped[str] = mapped_column(String, nullable=False)
    item_description: Mapped[str] = mapped_column(String, nullable=True)
    purchase_req_id: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    approval_attr = relationship(
        "Approval",
        back_populates="son_comment_attr",
        foreign_keys=[approvals_uuid]
    )

class JustificationTemplate(Base):
    __tablename__ = "justification_templates"
    code: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False) 