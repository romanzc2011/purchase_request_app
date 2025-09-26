import asyncio
import signal
import time
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import api.services.db_service as dbas
from sqlalchemy import select
from fastapi import HTTPException
import os
import sys
from api.settings import settings
from typing import Optional

"""
This file contains miscellaneous utility functions that are used throughout the project.

format_username: Formats the username to remove the ADU\ prefix.
run_in_thread: Runs a function in a thread @decorator.
"""

def error_handler(signum, frame):
    logger.warning("Services shutting down...")
    sys.exit(0)
#--------------------------------------------------------------------------------------------------
# FORMAT USERNAME
#--------------------------------------------------------------------------------------------------
def format_username(username: str) -> str:
    if username is None:
        return ""
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
    from api.services.db_service import SonComment, PurchaseRequestLineItem
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
    
    # -------------------------------------------------------
    # Get SonComments
    # -------------------------------------------------------
    
    # First, get line item UUIDs for this purchase request
    line_items_stmt = (
        select(PurchaseRequestLineItem.UUID)
        .where(PurchaseRequestLineItem.purchase_request_id == ID)
    )
    line_items_result = await db.execute(line_items_stmt)
    line_item_uuids = [row[0] for row in line_items_result.all()]
    
    # Get SonComments by line_item_uuid (more reliable)
    son_comments_stmt = (
        select(SonComment)
        .where(SonComment.line_item_uuid.in_(line_item_uuids))
        .where(SonComment.comment_text.is_not(None))
    )
    result = await db.execute(son_comments_stmt)
    son_comments = result.scalars().all()
    
    return additional_comments


from typing import Optional

async def price_change_allowed(
    db: AsyncSession,
    purchase_request_id: str,
    original_total_price: float,
    new_total_price: Optional[float] = None,
) -> bool:
    logger.debug(f"Original total price: {original_total_price}")
    logger.debug(f"New total price: {new_total_price}")

    try:
        has_price_updated = await dbas.get_has_price_updated(db, purchase_request_id)
        logger.debug(f"Has price updated: {has_price_updated}")
        
        # If no price has been updated yet, set baseline and allow
        if not has_price_updated:
            # Use the new_total_price as the baseline if original is 0
            baseline_price = original_total_price if original_total_price > 0 else (new_total_price or 0)
            
            if baseline_price > 0:
                # Set the baseline price (first non-zero price)
                await dbas.set_original_total_price(db, purchase_request_id, baseline_price)
                
                # Calculate and store allowed increase (10% or $100, whichever is smaller)
                allowed_increase_total = min(baseline_price * 0.10, 100.0)
                await dbas.set_allowed_increase_total(db, purchase_request_id, allowed_increase_total)
                
                logger.debug(f"Set baseline: original={baseline_price}, allowed_increase={allowed_increase_total}")
                return True
            else:
                # No baseline yet, allow any price
                return True
        
        # Price has been updated before, check against allowance
        allowed_increase_total = await dbas.get_allowed_increase_total(db, purchase_request_id)
        stored_original_price = await dbas.get_original_total_price(db, purchase_request_id)
        
        if new_total_price is None:
            return True  # No new price to validate
            
        # Use the stored original price as the baseline for comparison
        baseline_price = stored_original_price or original_total_price
        price_increase = new_total_price - baseline_price
        is_within_allowance = price_increase <= allowed_increase_total
        
        logger.debug(f"Baseline price: {baseline_price}")
        logger.debug(f"Price increase: {price_increase}")
        logger.debug(f"Allowed increase: {allowed_increase_total}")
        logger.debug(f"Within allowance: {is_within_allowance}")
        
        return is_within_allowance

    except Exception as e:
        logger.error(f"Error calculating price allowance: {e}")
        return False