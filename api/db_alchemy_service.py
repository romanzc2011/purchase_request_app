
from loguru import logger
from sqlalchemy import (create_engine, or_, Column, String, Integer,
                         Float, Boolean, Text, LargeBinary, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from pydantic_schemas import PurchaseRequestSchema, AppovalSchema
import json

# Create engine and base
engine = create_engine('sqlite:///db/purchase_request.db', echo=True)
Base = declarative_base()

# Define your session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

########################################################
## PURCHASE REQUEST
class PurchaseRequest(Base):
    __tablename__ = "purchase_request"

    ID: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    reqID: Mapped[str] = mapped_column(String, nullable=False)
    requester: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    phoneext: Mapped[int] = mapped_column(Integer, nullable=False)
    datereq: Mapped[str] = mapped_column(String)      
    dateneed: Mapped[str] = mapped_column(String)      
    orderType: Mapped[str] = mapped_column(String)
    fileAttachments: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    itemDescription: Mapped[str] = mapped_column(Text)
    justification: Mapped[str] = mapped_column(Text)
    addComments: Mapped[Optional[str]] = mapped_column(Text) 
    trainNotAval: Mapped[str] = mapped_column(Text, nullable=True)
    needsNotMeet: Mapped[str] = mapped_column(Text, nullable=True)
    budgetObjCode: Mapped[str] = mapped_column(String)
    fund: Mapped[str] = mapped_column(String)
    priceEach: Mapped[float] = mapped_column(Float)
    totalPrice: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    new_request: Mapped[bool] = mapped_column(Boolean)
    pending_approval: Mapped[bool] = mapped_column(Boolean)
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
## approval TABLE
class Approval(Base):
    __tablename__ =  "approval"

    #  Use the same ID as purchase_request, creating a one-to-one relationship
    ID: Mapped[str] = mapped_column(String, ForeignKey("purchase_request.ID"), primary_key=True, nullable=False)
    reqID: Mapped[str] = mapped_column(String, nullable=False)
    requester: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    budgetObjCode: Mapped[str] = mapped_column(String)
    fund: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    totalPrice: Mapped[float] = mapped_column(Float)
    priceEach: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String)
    new_request: Mapped[bool] = mapped_column(Boolean)
    pending_approval: Mapped[bool] = mapped_column(Boolean)
    approved: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String)

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
                Approval.fund.ilike(f"%{query}%"),
                Approval.budgetObjCode.ilike({f"%{query}%"})
            )
        ).all()
        return results
    finally:
        session.close()
        
## Get all data from Approval
def get_all_approval(db_session: Session):
    results = db_session.query(Approval).all()
    return results

# Insert data
def insert_data(processed_data, table):
    logger.info(f"Inserting data into {table}, data: {processed_data}")
    
    if not processed_data or not isinstance(processed_data, dict):
        raise ValueError("Processed data must be a non-empty dictionary")
    
    for key, value in processed_data.items():
        if isinstance(value, list):
            processed_data[key] = json.dumps(value)
    
    with next(get_db_session()) as db:
        if table == "purchase_request":
            new_obj = PurchaseRequest(**processed_data)
        elif table == "approval":
            new_obj = Approval(**processed_data)
        else:
            raise ValueError(f"Unsupported table: {table}")

        db.add(new_obj)
        db.commit()
        logger.info(f"Successfully inserted data into {table}")

# Retrieve data from single line
def fetch_single_row(self, model_class, columns: list, condition, params: dict):
    """
    model_class: SQLAlchemy ORM model (e.g., PurchaseRequest)
    columns: list of attributes (e.g., [PurchaseRequest.requester, PurchaseRequest.fund])
    condition: SQLAlchemy filter expression (e.g., PurchaseRequest.reqID == :req_id)
    params: dictionary of bind parameters (e.g., {"req_id": "REQ-001"})
    """
    
    if not columns or not isinstance(columns, list):
        raise ValueError("Columns must be a non-empty list")
    
    with get_db_session() as db:
        result = db.query(*columns).filter(condition).params(params).first()
        return result