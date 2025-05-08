from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime
from .db_service import Approval

def add_comment(db_session: Session, ID: str, comment: str) -> bool:
    """
    Add a comment to an approval record.
    
    Args:
        db_session: SQLAlchemy database session
        ID: The ID of the approval record
        comment: The comment to add
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        approval = db_session.query(Approval).filter(Approval.ID == ID).first()
        if not approval:
            logger.error(f"No approval found with ID: {ID}")
            return False
            
        # Get current date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_comment = f"[{current_datetime}] {comment}"
            
        # If there's an existing comment, append the new one
        if approval.addComments:
            approval.addComments = f"{approval.addComments}\n{formatted_comment}"
        else:
            approval.addComments = formatted_comment
            
        db_session.commit()
        logger.info(f"Successfully added comment to approval {ID}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding comment to approval {ID}: {e}")
        db_session.rollback()
        return False 