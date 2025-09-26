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
    original_price_each: float,
    new_price_each: Optional[float] = None,
    new_total_price: Optional[float] = None,
) -> bool:
    logger.debug(f"Original price each: {original_price_each}")
    logger.debug(f"New price each: {new_price_each}")
    logger.debug(f"New total price: {new_total_price}")

    try:
        has_price_updated = await dbas.get_has_price_updated(
            db, purchase_request_id, line_item_uuid
        )
        if not has_price_updated:
            # No prior “original” baseline yet → allow
            return True

        # Allowance per unit: +10% or $100 (see NOTE below about min vs max)
        allowed_increase_each = min(original_price_each * 0.10, 100.0)

        # Pull current quantity to evaluate total allowance correctly
        qty = await dbas.get_line_item_quantity(db, line_item_uuid)
        original_total = original_price_each * qty
        allowed_increase_total = allowed_increase_each * qty

        ok_each = (
            new_price_each is not None
            and (new_price_each - original_price_each) <= allowed_increase_each
        )

        ok_total = (
            new_total_price is not None
            and (new_total_price - original_total) <= allowed_increase_total
        )

        price_allowance_ok = ok_each or ok_total
        logger.info(f"Price allowance is ok: {price_allowance_ok}")
        return price_allowance_ok

    except Exception as e:
        logger.error(f"Error calculating price allowance: {e}")
        return False