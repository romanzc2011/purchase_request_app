from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import (create_engine, or_, Column, String, Integer,
                         Float, Boolean, Text, LargeBinary, ForeignKey, DateTime, Enum)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.inspection import inspect
from typing import Optional
import uuid
import enum

# Create engine and base
engine = create_engine('sqlite:///db/purchase_request.db', echo=False)
Base = declarative_base()
my_session = sessionmaker(engine)

###################################################################################################
##  LINE ITEM STATUS ENUMERATION
class LineItemStatusEnum(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    ON_HOLD = "on_hold"

###################################################################################################
## PURCHASE REQUEST
class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    UUID:            Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ID:              Mapped[str] = mapped_column(String, unique=False, nullable=False)
    requester:       Mapped[str] = mapped_column(String, nullable=False)
    phoneext:        Mapped[int] = mapped_column(Integer, nullable=False)
    datereq:         Mapped[str] = mapped_column(String)      
    dateneed:        Mapped[str] = mapped_column(String)      
    orderType:       Mapped[str] = mapped_column(String)
    fileAttachments: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    itemDescription: Mapped[str] = mapped_column(Text)
    justification:   Mapped[str] = mapped_column(Text)
    addComments:     Mapped[Optional[str]] = mapped_column(Text) 
    trainNotAval:    Mapped[bool] = mapped_column(Boolean, nullable=True)
    needsNotMeet:    Mapped[bool] = mapped_column(Boolean, nullable=True)
    budgetObjCode:   Mapped[str] = mapped_column(String)
    fund:            Mapped[str] = mapped_column(String)
    newRequest:      Mapped[bool] = mapped_column(Boolean)
    pendingApproval: Mapped[bool] = mapped_column(Boolean)
    approved:        Mapped[bool] = mapped_column(Boolean)
    status:          Mapped[str] = mapped_column(String, nullable=False)
    priceEach:       Mapped[float] = mapped_column(Float)
    totalPrice:      Mapped[float] = mapped_column(Float)
    location:        Mapped[str] = mapped_column(String)
    quantity:        Mapped[int] = mapped_column(Integer)
    createdTime:     Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    __searchable__ = ['ID', 'IRQ1_ID', 'requester', 'budgetObjCode', 'fund',
                     'location', 'quantity', 'priceEach', 'totalPrice', 'status', 'trainNotAval', 'needsNotMeet']

    # Relationships
    approval = relationship("Approval", back_populates="purchase_request", uselist=False)
    line_item_status = relationship("LineItemStatus", back_populates="purchase_request", uselist=False)
    comments = relationship("SonComments", back_populates="purchase_request")

###################################################################################################
## approval TABLE
class Approval(Base):
    __tablename__ =  "approval"
    __searchable__ = ['ID', 'IRQ1_ID', 'CO', 'requester', 'budgetObjCode', 'fund', 'trainNotAval', 'needsNotMeet',
                      'quantity', 'totalPrice', 'priceEach', 'location', 'newRequest', 
                      'approved', 'pendingApproval', 'status', 'createdTime', 'approvedTime', 'deniedTime']

    # Sequential ID for user-facing operations
    ID:              Mapped[str] = mapped_column(String, ForeignKey("purchase_requests.ID"), primary_key=True, nullable=False)
    IRQ1_ID:         Mapped[str] = mapped_column(String, nullable=True, unique=True)
    requester:       Mapped[str] = mapped_column(String, nullable=False)
    CO:              Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phoneext:        Mapped[int] = mapped_column(Integer, nullable=False)
    datereq:         Mapped[str] = mapped_column(String)      
    dateneed:        Mapped[str] = mapped_column(String)      
    orderType:       Mapped[str] = mapped_column(String)
    fileAttachments: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    itemDescription: Mapped[str] = mapped_column(Text)
    justification:   Mapped[str] = mapped_column(Text)
    addComments:     Mapped[Optional[str]] = mapped_column(Text) 
    trainNotAval:    Mapped[bool] = mapped_column(Boolean, nullable=True)
    needsNotMeet:    Mapped[bool] = mapped_column(Boolean, nullable=True)
    budgetObjCode:   Mapped[str] = mapped_column(String)
    fund:            Mapped[str] = mapped_column(String)
    priceEach:       Mapped[float] = mapped_column(Float)
    totalPrice:      Mapped[float] = mapped_column(Float)
    location:        Mapped[str] = mapped_column(String)
    quantity:        Mapped[int] = mapped_column(Integer)
    newRequest:      Mapped[bool] = mapped_column(Boolean)
    approved:        Mapped[bool] = mapped_column(Boolean)
    pendingApproval: Mapped[bool] = mapped_column(Boolean)
    status:          Mapped[str] = mapped_column(String, nullable=False)
    createdTime:     Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    # Relationship
    purchase_request = relationship("PurchaseRequest", back_populates="approval", uselist=False)
    comments = relationship("SonComments", back_populates="approval")

###################################################################################################
## review TABLE
class LineItemStatus(Base):
    __tablename__ = "line_item_status"
    id:                     Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_request_id:    Mapped[str] = mapped_column(String, ForeignKey("purchase_requests.ID"), nullable=False)
    status:                 Mapped[LineItemStatus] = mapped_column(Enum(LineItemStatus), nullable=False)
    hold_until:             Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_updated:           Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by:             Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationship
    purchase_request = relationship("PurchaseRequest", back_populates="line_item_status", uselist=False)

###################################################################################################
## LINE ITEM COMMENTS TABLE
class SonComments(Base):
    __tablename__ = "son_comments"
    
    id:                  Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_request_id: Mapped[str] = mapped_column(String, ForeignKey("purchase_requests.ID"), nullable=False)
    approval_id:         Mapped[str] = mapped_column(String, ForeignKey("approval.ID"), nullable=False)
    comment_text:        Mapped[str] = mapped_column(Text)
    created_at:          Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    son_requester:       Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    purchase_request = relationship("PurchaseRequest", back_populates="comments")
    approval = relationship("Approval", back_populates="comments")

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
    return db_session.query(Approval).all()

def get_approval_by_id(db_session: Session, ID: str):
    return db_session.query(Approval).filter(Approval.ID == ID).all()

###################################################################################################
# Insert data
def insert_data(data, table):
    # Get last id if there is one 
    logger.info(f"Inserting data into {table}: {data}")
    
    if not data:
        raise ValueError("Data must be a non-empty dictionary")
    
    # Pick the right table
    match table:
        case "purchase_requests":
            model = PurchaseRequest
        case "approval":
            model = Approval
        case "line_item_status":
            model = LineItemStatus
        case "son_comments":
            model = SonComments
        case _:
            raise ValueError(f"Unsupported table: {table}")
        
    # Strip out keys that are not in model
    valid_cols = set(inspect(model).columns.keys())
    filtered_data = {k: v for k, v in data.items() if k in valid_cols}
    
    # Construct, add, build
    with next(get_session()) as db:
        obj = model(**filtered_data)
        db.add(obj)
        db.commit()
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
# Update data
###################################################################################################
def update_data(ID, table, **kwargs):
    logger.info(f"Updating {table} with ID {ID}, data: {kwargs}")
    
    if not kwargs or not isinstance(kwargs, dict):
        raise ValueError("Update data must be a non-empty dictionary")
    
    with next(get_session()) as db:
        if table == "purchase_requests":
            # Try sequential ID first
            obj = db.query(PurchaseRequest).filter(PurchaseRequest.ID == ID).first()
            if not obj:
                # If not found, try uuid
                obj = db.query(PurchaseRequest).filter(PurchaseRequest.UUID == ID).first()
        elif table == "approval":
            # Try sequential ID first
            obj = db.query(Approval).filter(Approval.ID == ID).first()
            if not obj:
                # If not found, try uuid
                obj = db.query(Approval).filter(Approval.UUID == ID).first()
        else:
            raise ValueError(f"Unsupported table: {table}")
        
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    # Special handling for uuid field
                    if key == "UUID" and value:
                        # Check if the uuid already exists in the database
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
    
    with get_session() as db:
        result = db.query(*columns).filter(condition).params(params).first()
        return result
    
###################################################################################################
# Get last 4 digits of the ID from the database
###################################################################################################
def _get_last_id() -> Optional[str]:
    """
    Return the full most‐recent PurchaseRequest.ID (e.g. "20250414-0007"),
    or None if the table is empty.
    """
    with next(get_session()) as db:
        # Query the Approval table instead of PurchaseRequest
        row = (
            db.query(Approval.ID)
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
# Update data by uuid
def update_data_by_uuid(uuid: str, table: str, **kwargs):
    logger.info(f"Updating {table} with uuid {uuid}, data: {kwargs}")
    
    if not kwargs or not isinstance(kwargs, dict):
        raise ValueError("Update data must be a non-empty dictionary")
    
    with next(get_session()) as db:
        if table == "purchase_requests":
            obj = db.query(PurchaseRequest).filter(PurchaseRequest.uuid == uuid).first()
        elif table == "approval":
            obj = db.query(Approval).filter(Approval.uuid == uuid).first()
        else:
            raise ValueError(f"Unsupported table: {table}")
        
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
                else:
                    raise ValueError(f"Invalid field: {key}")
            
            db.commit()
            logger.info(f"Successfully updated {table} with uuid {uuid}")
        else:
            logger.error(f"Object with uuid {uuid} not found in {table}")
            raise ValueError(f"Object with uuid {uuid} not found in {table}")
            
###################################################################################################
# Get uuids for multiple IDs
###################################################################################################
def get_uuids_by_ids(db_session: Session, ids: list):
    """
    Get uuids for multiple IDs.
    Returns a dictionary mapping IDs to uuids.
    """
    logger.info(f"Getting uuids for {len(ids)} IDs")
    
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

            
