from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.comment_service import add_comment
from ..dependencies import get_db

router = APIRouter()

@router.post("/add_comment/{ID}")
async def add_comment_endpoint(ID: str, comment: str, db: Session = Depends(get_db)):
    """
    Add a comment to an approval record.
    
    Args:
        ID: The ID of the approval record
        comment: The comment to add
        
    Returns:
        dict: Success message or error
    """
    success = add_comment(db, ID, comment)
    if not success:
        raise HTTPException(status_code=404, detail="Failed to add comment")
    return {"message": "Comment added successfully"} 