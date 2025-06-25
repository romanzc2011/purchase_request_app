import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import api.services.db_service as dbas

"""
This file contains miscellaneous utility functions that are used throughout the project.

format_username: Formats the username to remove the ADU\ prefix.
run_in_thread: Runs a function in a thread @decorator.
"""

#--------------------------------------------------------------------------------------------------
# FORMAT USERNAME
#--------------------------------------------------------------------------------------------------
def format_username(username: str) -> str:
    raw_name = username.lower()
    if "adu\\" in raw_name:
        raw_name = raw_name.replace("adu\\", "")
    return raw_name

#--------------------------------------------------------------------------------------------------
# RUN IN THREAD
#--------------------------------------------------------------------------------------------------
def run_in_thread(fn):
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)
    return wrapper

#--------------------------------------------------------------------------------------------------
# GET JUSTIFICATIONS
#--------------------------------------------------------------------------------------------------
"""
Utility function to get justifications from the database for PDFs and emails
"""
async def get_justifications_and_comments(db: AsyncSession, ID: str) -> list[str]:
    codes = await dbas.get_justifications_by_id(db, ID)
    templates = await dbas.get_justification_templates(db)
    
    justification_codes = []
    for train_not_aval, needs_not_meet in codes:
        if train_not_aval:
            justification_codes.append("NOT_AVAILABLE")
        if needs_not_meet:
            justification_codes.append("NEEDS_NOT_MEET")
            
    # Remove duplicates
    justification_codes = list(set(justification_codes))
    additional_comments = [
        templates.get(code, f"<no template for {code}>")
        for code in justification_codes
    ]
    logger.info(f"Justifications: {additional_comments}")
    
    # -------------------------------------------------------
    # Get SonComments
    # -------------------------------------------------------
    
    
    
    
    return additional_comments