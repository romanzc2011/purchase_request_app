from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import (create_engine, or_, Column, String, Integer,
                         Float, Boolean, Text, LargeBinary, ForeignKey, DateTime)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import json

# Create engine and base
engine = create_engine('sqlite:///db/purchase_request.db', echo=True)
Base = declarative_base()
my_session = sessionmaker(engine)

###################################################################################################
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
    newRequest: Mapped[bool] = mapped_column(Boolean)
    pendingApproval: Mapped[bool] = mapped_column(Boolean)
    approved: Mapped[bool] = mapped_column(Boolean)
    createdTime: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)

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

###################################################################################################
## approval TABLE
class Approval(Base):
    __tablename__ =  "approval"
    __searchable__ = ['ID', 'reqID', 'requester', 'recipient', 'budgetObjCode','fund', 
                      'quantity', 'totalPrice', 'priceEach', 'location', 'newRequest', 
                      'approved', 'pendingApproval', 'createdTime', 'approvedTime', 'deniedTime']

    #  Use the same ID as purchase_request, creating a one-to-one relationship
    ID: Mapped[str] = mapped_column(String, ForeignKey("purchase_request.ID"), primary_key=True, nullable=False)
    reqID: Mapped[str] = mapped_column(String, nullable=False)
    requester: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    budgetObjCode: Mapped[str] = mapped_column(String)
    fund: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    itemDescription: Mapped[str] = mapped_column(Text)
    justification: Mapped[str] = mapped_column(Text)
    totalPrice: Mapped[float] = mapped_column(Float)
    priceEach: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String)
    newRequest: Mapped[bool] = mapped_column(Boolean)
    pendingApproval: Mapped[bool] = mapped_column(Boolean)
    approved: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String)
    createdTime: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    approvedTime: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deniedTime: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Link back to PurchaseRequest without cascade here.
    purchase_request = relationship(
        "PurchaseRequest",
        back_populates="approval",
        uselist=False
    )
    
Base.metadata.create_all(engine)
my_session = sessionmaker(bind=engine)

###################################################################################################
 ## Create session for functions/queries
def get_session():
    db = my_session()
    try:
        yield db
    finally:
        db.close()

###################################################################################################   
## Get all data from Approval
def get_all_approval(db_session: Session):
    results = db_session.query(Approval).all()
    return results

###################################################################################################
# Insert data
def insert_data(processed_data, table):
    logger.info(f"Inserting data into {table}, data: {processed_data}")
    
    if not processed_data or not isinstance(processed_data, dict):
        raise ValueError("Processed data must be a non-empty dictionary")
    
    for key, value in processed_data.items():
        if isinstance(value, list):
            processed_data[key] = json.dumps(value)
    
    with next(get_session()) as db:
        if table == "purchase_request":
            new_obj = PurchaseRequest(**processed_data)
        elif table == "approval":
            new_obj = Approval(**processed_data)
        else:
            raise ValueError(f"Unsupported table: {table}")

        db.add(new_obj)
        db.commit()
        logger.info(f"Successfully inserted data into {table}")

###################################################################################################
# Get status of request from Approval table
def get_status_by_id(db_session: Session, ID: str):
    logger.info(f"Fetching status for ID: {ID}")
    
    if not ID:
        raise ValueError("ID must be a non-empty string")
    
    result = db_session.query(Approval).filter(Approval.ID == ID).first()
    
    if result:
        return result.status
    else:
        logger.error(f"Object with ID {ID} not found in Approval table")
        raise ValueError(f"Object with ID {ID} not found in Approval table")


###################################################################################################
# Update data
def update_data(ID, table, **kwargs):
    logger.info(f"Updating {table} with ID {ID}, data: {kwargs}")
    
    if not kwargs or not isinstance(kwargs, dict):
        raise ValueError("Update data must be a non-empty dictionary")
    
    with next(get_session()) as db:
        if table == "purchase_request":
            obj = db.query(PurchaseRequest).filter(PurchaseRequest.ID == ID).first()
        elif table == "approval":
            obj = db.query(Approval).filter(Approval.ID == ID).first()
        else:
            raise ValueError(f"Unsupported table: {table}")
        
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
                else:
                    raise ValueError(f"Invalid field: {key}")
            
            db.commit()
            logger.info(f"Successfully updated {table} with ID {ID}")
        else:
            logger.error(f"Object with ID {ID} not found in {table}")
            raise ValueError(f"Object with ID {ID} not found in {table}")
        
###################################################################################################
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
    
    with get_session() as db:
        result = db.query(*columns).filter(condition).params(params).first()
        return result