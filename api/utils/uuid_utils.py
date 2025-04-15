from loguru import logger
from sqlalchemy.orm import Session
import services.db_service as dbas

# UUID cache to improve performance
_uuid_cache = {}

def get_uuid_by_id(db_session: Session, ID: str):
    """
    Get UUID by ID with caching for better performance.
    This function can be imported by other modules.
    """
    # Check cache first
    if ID in _uuid_cache:
        logger.info(f"UUID cache hit for ID: {ID}")
        return _uuid_cache[ID]
    
    # If not in cache, get from database
    try:
        # First try to find by sequential ID
        result = db_session.query(dbas.Approval).filter(dbas.Approval.ID == ID).first()
        if result:
            uuid = result.UUID
            # Store in cache
            _uuid_cache[ID] = uuid
            logger.info(f"Added UUID to cache for ID: {ID}")
            return uuid
        else:
            logger.warning(f"No UUID found for ID: {ID}")
            return None
    except Exception as e:
        logger.error(f"Error getting UUID for ID {ID}: {e}")
        return None

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

def clear_uuid_cache():
    """
    Clear the UUID cache.
    """
    global _uuid_cache
    _uuid_cache = {}
    logger.info("UUID cache cleared") 