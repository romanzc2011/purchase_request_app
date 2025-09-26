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
    line_item_uuid: str,
    original_total_price: float,
    new_total_price: Optional[float] = None,
) -> bool:
    logger.debug(f"Original total price: {original_total_price}")
    logger.debug(f"New total price: {new_total_price}")

    try:
        # Get the total of ALL line items in the purchase request
        total_order_value = await dbas.get_total_order_value(db, purchase_request_id)
        logger.debug(f"Total order value: {total_order_value}")
        
        # Check if ALL line items have been price updated
        total_line_items = await dbas.get_line_item_count(db, purchase_request_id)
        price_updated_count = await dbas.get_price_updated_count(db, purchase_request_id)
        all_items_updated = (total_line_items > 0 and price_updated_count == total_line_items)
        
        logger.debug(f"Total line items: {total_line_items}")
        logger.debug(f"Price updated count: {price_updated_count}")
        logger.debug(f"All items updated: {all_items_updated}")
        
        # If not all items have been price updated yet, allow any price
        if not all_items_updated:
            logger.debug("Not all items price updated yet, allowing any price")
            return True
        
        # Check if baseline has been set yet
        baseline_exists = await dbas.get_order_baseline_exists(db, purchase_request_id)
        
        # If all items updated but no baseline set yet, set it now
        if not baseline_exists:
            if total_order_value > 0:
                logger.debug("Setting order baseline")
                logger.debug(f"Total order value: {total_order_value}")
                # Set the baseline for the entire order
                await dbas.set_order_baseline(db, purchase_request_id, total_order_value)
                
                # Calculate and store allowed increase (10% or $100, whichever is smaller)
                allowed_increase_total = min(total_order_value * 0.10, 100.0)
                await dbas.set_order_allowed_increase(db, purchase_request_id, allowed_increase_total)
                
                logger.debug(f"Set order baseline: original={total_order_value}, allowed_increase={allowed_increase_total}")
                return True
            else:
                # No baseline yet, allow any price
                return True
        
        # Price has been updated before, check against order-level allowance
        allowed_increase_total = await dbas.get_order_allowed_increase(db, purchase_request_id)
        order_baseline = await dbas.get_order_baseline(db, purchase_request_id)
        
        if new_total_price is None:
            return True  # No new price to validate
            
        # Calculate the new total order value with this change
        new_total_order_value = await dbas.get_new_total_order_value(db, purchase_request_id, line_item_uuid, new_total_price)
        order_increase = new_total_order_value - order_baseline
        is_within_allowance = order_increase <= allowed_increase_total
        
        logger.debug(f"Order baseline: {order_baseline}")
        logger.debug(f"New total order: {new_total_order_value}")
        logger.debug(f"Order increase: {order_increase}")
        logger.debug(f"Allowed increase: {allowed_increase_total}")
        logger.debug(f"Within allowance: {is_within_allowance}")
        
        return is_within_allowance

    except Exception as e:
        logger.error(f"Error calculating price allowance: {e}")
        return False