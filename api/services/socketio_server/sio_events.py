from api.services.socketio_server.sio_instance import sio
from loguru import logger
from typing import Any, Dict, Optional, Union
from api.schemas.ldap_schema import LDAPUser
from api.services.socketio_server.socket_state import user_sids, sid_user as sid_user_map
from fastapi import Depends
from api.dependencies.pras_dependencies import auth_service
from api.utils.misc_utils import format_username
from api.schemas.enums import SIOEvents

RESET_PROGRESS_BAR = False

async def decode_and_validate_token(token: str) -> LDAPUser:
    return await auth_service.get_current_user(token)

# SocketIO events
@sio.event
async def connect(sid, environ, auth):
    user = await decode_and_validate_token((auth or {}).get("token"))
    if not user:
        return None
    username = user.username
    user_sids.setdefault(username, set())
    user_sids[username].add(sid)
    sid_user_map[sid] = username
    logger.debug(f"socketio: connect {sid} {username}")
    return sid_user_map

@sio.event
async def progress_update(sid: str, payload: Dict[str, Any]) -> None:
    await sio.emit(SIOEvents.PROGRESS_UPDATE.value, payload, to=sid)
    

@sio.event
async def start_toast(sid: str, percent: int = 0) -> None:
    await sio.emit(SIOEvents.START_TOAST.value, {"percent_complete": percent}, to=sid)
    if percent == 100:
        RESET_PROGRESS_BAR = True
        
def get_reset_progress_bar() -> bool:
    return RESET_PROGRESS_BAR

def get_user_sid(user_or_name: Union[str, "LDAPUser", None]) -> Optional[str]:
    from api.services.socketio_server.socket_state import user_sids

    if user_or_name is None:
        logger.warning("get_user_sid called with None user")
        return None

    username = getattr(user_or_name, "username", user_or_name)
    if not isinstance(username, str) or not username:
        logger.warning(f"get_user_sid: invalid username payload: {user_or_name!r}")
        return None

    sid_set = user_sids.get(username, set())
    if not sid_set:
        logger.warning(f"No SocketIO session found for user {username}")
        return None

    sid = next(iter(sid_set))
    logger.debug(f"Found SocketIO session {sid} for user {username}")
    return sid

@sio.event
async def disconnect(sid):
    logger.debug(f"socketio: disconnect {sid}")
    
    # Clean up user session mappings
    if sid in sid_user_map:
        username = sid_user_map[sid]
        if username in user_sids:
            user_sids[username].discard(sid)
            # Remove empty user entries
            if not user_sids[username]:
                del user_sids[username]
        del sid_user_map[sid]
        logger.debug(f"Cleaned up session mappings for user {username}")

# --------------------------------------------------------------
# MESSAGE EVENT
# --------------------------------------------------------------
"""
# MESSAGE EVENT
# This event sends regular data messages to client. Data to send will include non specific/general messages 
 and/or status updates, etc. 
"""
@sio.on(SIOEvents.MESSAGE_EVENT.value)
async def message_event(sid, data):
    logger.debug("socketio: message_event", sid)
    if get_reset_progress_bar():
        await sio.emit(SIOEvents.RESET_DATA.value, {"message": "Resetting progress bar"}, to=sid)
        RESET_PROGRESS_BAR = False
    await sio.emit(SIOEvents.MESSAGE_EVENT.value, {"message": data}, to=sid)
    
@sio.on(SIOEvents.RESET_DATA.value)
async def reset_data(sid):
    logger.debug("socketio: reset_data", sid)
    
@sio.on(SIOEvents.ERROR_EVENT.value)
async def error_event(sid, data):
    logger.debug("socketio: error_event", sid)
    await sio.emit(SIOEvents.ERROR_EVENT.value, {"message": data}, to=sid)
    
@sio.on(SIOEvents.SEND_ORIGINAL_PRICE.value)
async def send_original_price(sid, data):
    logger.debug("socketio: send_original_price", sid)
    await sio.emit(SIOEvents.SEND_ORIGINAL_PRICE.value, {"message": data}, to=sid)
    
    
