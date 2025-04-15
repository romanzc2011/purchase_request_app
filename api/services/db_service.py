from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import (create_engine, or_, Column, String, Integer,
                         Float, Boolean, Text, LargeBinary, ForeignKey, DateTime)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import uuid

# Create engine and base
engine = create_engine('sqlite:///db/purchase_request.db', echo=True)
Base = declarative_base()
my_session = sessionmaker(engine)

###################################################################################################
## PURCHASE REQUEST
class PurchaseRequest(Base):
    __tablename__ = "purchase_request"

    # UUID as primary key
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Sequential ID for user-facing operations
    ID: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    reqID: Mapped[str] = mapped_column(String, nullable=False)
    requester: Mapped[str] = mapped_column(String, nullable=False)
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
        uselist=False
        
    )

    def __repr__(self):
        return f"<PurchaseRequest(reqID='{self.reqID}', requester='{self.requester}')>"

###################################################################################################
## approval TABLE
class Approval(Base):
    __tablename__ =  "approval"
    __searchable__ = ['ID', 'reqID', 'requester', 'budgetObjCode', 'fund', 
                      'quantity', 'totalPrice', 'priceEach', 'location', 'newRequest', 
                      'approved', 'pendingApproval', 'status', 'createdTime', 'approvedTime', 'deniedTime']

    # UUID as primary key
    UUID: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Sequential ID for user-facing operations
    ID: Mapped[str] = mapped_column(String, ForeignKey("purchase_request.ID"), nullable=False, unique=True)
    reqID: Mapped[str] = mapped_column(String, nullable=False)
    requester: Mapped[str] = mapped_column(String, nullable=False)
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
    status: Mapped[str] = mapped_column(String, nullable=False)
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
def insert_data(data, table):
    # Get last id if there is one 
    logger.info(f"Inserting data into {table}: {data}")
    
    if not data or not isinstance(data, dict):
        raise ValueError("Data must be a non-empty dictionary")
    
    with next(get_session()) as db:
        try:
            if table == "purchase_request":
                # Create new PurchaseRequest with UUID
                data['ID'] = get_next_request_id()
                obj = PurchaseRequest(**data)
                db.add(obj)
            elif table == "approval":
                # Create new Approval with UUID
                obj = Approval(**data)
                db.add(obj)
            else:
                raise ValueError(f"Unsupported table: {table}")
            
            db.commit()
            logger.info(f"Successfully inserted data into {table}")
            return obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error inserting data into {table}: {e}")
            raise

###################################################################################################
# Get status of request from Approval table
def get_status_by_id(db_session: Session, ID: str):
    logger.info(f"Fetching status for ID: {ID}")
    
    if not ID:
        raise ValueError("ID must be a non-empty string")
    
    # First try to find by sequential ID
    result = db_session.query(Approval).filter(Approval.ID == ID).first()
    if not result:
        # If not found, try UUID
        result = db_session.query(Approval).filter(Approval.UUID == ID).first()
    
    if result:
        return result.status
    else:
        logger.error(f"Object with ID {ID} not found in Approval table")
        raise ValueError(f"Object with ID {ID} not found in Approval table")
    
###################################################################################################
# Get requester from Approval table by UUID
def get_requester_by_uuid(db_session: Session, uuid: str):
    logger.info(f"Fetching requester for UUID: {uuid}")
    
    # Query the Approval table to get the requester field for the given UUID
    result = db_session.query(Approval.requester).filter(Approval.UUID == uuid).first()
    logger.info(f"Requester: {result}")
    
    if result:
        return result[0]  # Return just the requester string
    else:
        logger.warning(f"No requester found for UUID: {uuid}")
        return None

###################################################################################################
# UUID cache to improve performance
_uuid_cache = {}

# Get UUID by ID with caching
def get_uuid_by_id_cached(db_session: Session, ID: str):
    """
    Get UUID by ID with caching for better performance.
    """
    # Check cache first
    if ID in _uuid_cache:
        logger.info(f"UUID cache hit for ID: {ID}")
        return _uuid_cache[ID]
    
    # If not in cache, get from database
    uuid = get_uuid_by_id(db_session, ID)
    
    # Store in cache if found
    if uuid:
        _uuid_cache[ID] = uuid
        logger.info(f"Added UUID to cache for ID: {ID}")
    
    return uuid

###################################################################################################
# Get UUID by ID
def get_uuid_by_id(db_session: Session, ID: str):
    return db_session.query(Approval.UUID).filter(Approval.ID == ID).first()

###################################################################################################
# Update data
def update_data(ID, table, **kwargs):
    logger.info(f"Updating {table} with ID {ID}, data: {kwargs}")
    
    if not kwargs or not isinstance(kwargs, dict):
        raise ValueError("Update data must be a non-empty dictionary")
    
    with next(get_session()) as db:
        if table == "purchase_request":
            # Try sequential ID first
            obj = db.query(PurchaseRequest).filter(PurchaseRequest.ID == ID).first()
            if not obj:
                # If not found, try UUID
                obj = db.query(PurchaseRequest).filter(PurchaseRequest.UUID == ID).first()
        elif table == "approval":
            # Try sequential ID first
            obj = db.query(Approval).filter(Approval.ID == ID).first()
            if not obj:
                # If not found, try UUID
                obj = db.query(Approval).filter(Approval.UUID == ID).first()
        else:
            raise ValueError(f"Unsupported table: {table}")
        
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    # Special handling for UUID field
                    if key == "uuid" and value:
                        # Check if the UUID already exists in the database
                        existing = db.query(PurchaseRequest).filter(PurchaseRequest.UUID == value).first()
                        if existing and existing.UUID != obj.UUID:
                            logger.warning(f"UUID {value} already exists in the database")
                            continue
                    
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
    
###################################################################################################
# Get last 4 digits of the ID from the database
def _get_last_id() -> Optional[str]:
    """
    Return the full most‐recent PurchaseRequest.ID (e.g. "20250414-0007"),
    or None if the table is empty.
    """
    with next(get_session()) as db:
        row = (
            db.query(PurchaseRequest.ID)
            .order_by(PurchaseRequest.ID.desc())
            .limit(1)
            .first()
        )
        # Return just the ID string, not the tuple
        return row[0] if row else None
    
###################################################################################################
# Get next  request ID
def get_next_request_id() -> str:
    """
    Build the next ID in "YYYYMMDD-XXXX" format:
    - If today's date ≠ last ID's date, start at 0001
    - Otherwise increment the last 4‑digit suffix
    """
    today = datetime.now().strftime("%Y%m%d")
    last_id = _get_last_id()
    
    if not last_id:
        logger.info("No previous IDs found, starting with 0001")
        next_suffix = 1
    else:
        try:
            parts = last_id.split('-', 1)
            if len(parts) != 2:
                logger.warning(f"Invalid ID format: {last_id}, starting with 0001")
                next_suffix = 1
            else:
                try:
                    last_suffix = int(parts[1])
                    next_suffix = last_suffix + 1
                    logger.info(f"Last ID: {last_id}, next suffix: {next_suffix}")
                except ValueError:
                    logger.warning(f"Invalid suffix in ID: {last_id}, starting with 0001")
                    next_suffix = 1
        except Exception as e:
            logger.error(f"Error processing last ID: {e}, starting with 0001")
            next_suffix = 1
    
    return f"{today}-{next_suffix:04d}"
            
###################################################################################################
# Get status of request from Approval table by UUID
def get_status_by_uuid(db_session: Session, uuid: str):
    logger.info(f"Fetching status for UUID: {uuid}")
    
    if not uuid:
        raise ValueError("UUID must be a non-empty string")
    
    result = db_session.query(Approval.status).filter(Approval.UUID == uuid).first()
    
    if result:
        return result[0]  # Return just the status string
    else:
        logger.warning(f"No status found for UUID: {uuid}")
        return None

###################################################################################################
# Update data by UUID
def update_data_by_uuid(uuid: str, table: str, **kwargs):
    logger.info(f"Updating {table} with UUID {uuid}, data: {kwargs}")
    
    if not kwargs or not isinstance(kwargs, dict):
        raise ValueError("Update data must be a non-empty dictionary")
    
    with next(get_session()) as db:
        if table == "purchase_request":
            obj = db.query(PurchaseRequest).filter(PurchaseRequest.UUID == uuid).first()
        elif table == "approval":
            obj = db.query(Approval).filter(Approval.UUID == uuid).first()
        else:
            raise ValueError(f"Unsupported table: {table}")
        
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
                else:
                    raise ValueError(f"Invalid field: {key}")
            
            db.commit()
            logger.info(f"Successfully updated {table} with UUID {uuid}")
        else:
            logger.error(f"Object with UUID {uuid} not found in {table}")
            raise ValueError(f"Object with UUID {uuid} not found in {table}")
            
###################################################################################################
# Get UUIDs for multiple IDs
def get_uuids_by_ids(db_session: Session, ids: list):
    """
    Get UUIDs for multiple IDs.
    Returns a dictionary mapping IDs to UUIDs.
    """
    logger.info(f"Getting UUIDs for {len(ids)} IDs")
    
    result = {}
    for id in ids:
        uuid = get_uuid_by_id(db_session, id)
        if uuid:
            result[id] = uuid
    
    return result
            
        
