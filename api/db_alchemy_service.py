
from sqlalchemy import (create_engine, or_, Column, String, Integer,
                         Float, Boolean, Text, LargeBinary, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

# Create engine and base
engine = create_engine('sqlite:///db/purchase_requests.db', echo=True)
Base = declarative_base()

# Define your session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

########################################################
## PURCHASE REQUEST
class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    ID: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    reqID: Mapped[str] = mapped_column(String, nullable=False)
    requester: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    phoneext: Mapped[int] = mapped_column(Integer, nullable=False)
    datereq: Mapped[str] = mapped_column(String)      # Now required
    dateneed: Mapped[str] = mapped_column(String)      # Now required
    orderType: Mapped[str] = mapped_column(String)
    fileAttachments: Mapped[bytes] = mapped_column(LargeBinary)
    itemDescription: Mapped[str] = mapped_column(Text)
    justification: Mapped[str] = mapped_column(Text)
    addComments: Mapped[Optional[str]] = mapped_column(Text)  # Remains optional
    trainNotAval: Mapped[str] = mapped_column(Text)
    needsNotMeet: Mapped[str] = mapped_column(Text)
    budgetObjCode: Mapped[str] = mapped_column(String)
    fund: Mapped[str] = mapped_column(String)
    priceEach: Mapped[float] = mapped_column(Float)
    totalPrice: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    new_request: Mapped[bool] = mapped_column(Boolean)
    approved: Mapped[bool] = mapped_column(Boolean)

     # Set up a one-to-one relationship with Approval on the parent side
    approval = relationship(
        "Approval",
        cascade="all, delete-orphan",
        back_populates="purchase_request",
        uselist=False,
        single_parent=True  # Ensures that each PurchaseRequest has at most one Approval.
    )

    def __repr__(self):
        return f"<PurchaseRequest(reqID='{self.reqID}', requester='{self.requester}', recipient='{self.recipient}')>"


########################################################
## APPROVALS TABLE
class Approval(Base):
    __tablename__ =  "approvals"

    #  Use the same ID as purchase_requests, creating a one-to-one relationship
    ID: Mapped[str] = mapped_column(String, ForeignKey("purchase_requests.ID"), primary_key=True, nullable=False)
    reqID: Mapped[str] = mapped_column(String, nullable=False)
    requester: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    budgetObjCode: Mapped[str] = mapped_column(String)
    fund: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    totalPrice: Mapped[float] = mapped_column(Float)
    priceEach: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    new_request: Mapped[str] = mapped_column(String)

    # Link back to PurchaseRequest without cascade here.
    purchase_request = relationship(
        "PurchaseRequest",
        back_populates="approval",
        uselist=False
    )

    def __repr__(self):
        return (f"<Approval(reqID='{self.reqID}', requester='{self.requester}', "
            f"recipient='{self.recipient}', budgetObjCode='{self.budgetObjCode}', "
            f"status='{self.status}')>")
    
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

 ## Create session for functions/queries
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 ## Search for data
def search_results(query: str):
    session = SessionLocal()
    try:
        results = session.query(Approval).filter(
            or_(
                Approval.requester.ilike(f"%{query}%"),
                Approval.recipient.ilike(f"%{query}%"),
                Approval.fund.ilike(f"%{query}%")
            )
        ).all()
        return results
    finally:
        session.close()
        
## Get all data from Approvals
def get_all_approvals(db_session: Session):
    results = db_session.query(Approval).all()
    return results
