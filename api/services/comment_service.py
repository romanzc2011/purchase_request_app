from sqlalchemy.orm import Session
from sqlalchemy import select
from loguru import logger
from datetime import datetime
from .db_service import Approval, PurchaseRequest
import api.services.db_service as dbas

def add_comment(db_session: Session, id: str, comment: str) -> bool:
    """
    Add a comment to an approval record.
    
    Args:
        db_session: SQLAlchemy database session
        id: The id of the approval record
        comment: The comment to add
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        approval = db_session.query(Approval).filter(Approval.id == id).first()
        if not approval:
            logger.error(f"No approval found with id: {id}")
            return False
            
        # Get current date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_comment = f"[{current_datetime}] {comment}"
            
        # If there's an existing comment, append the new one
        if approval.add_comments:
            approval.add_comments = f"{approval.add_comments}, {formatted_comment}"
        else:
            approval.add_comments = formatted_comment
            
        db_session.commit()
        logger.info(f"Successfully added comment to approval {id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding comment to approval {id}: {e}")
        db_session.rollback()
        return False 
    
def get_add_comments(db_session: Session, id: str) -> list[str]:
    """Get additional comments by id"""
    stmt = (
        select(PurchaseRequest.add_comments)
        .join(Approval, PurchaseRequest.id == Approval.id)
        .where(PurchaseRequest.add_comments.is_not(None))
        .where(PurchaseRequest.id == id)
    )
    add_comments: list[str] = db_session.scalars(stmt).all()
    return add_comments
    
    