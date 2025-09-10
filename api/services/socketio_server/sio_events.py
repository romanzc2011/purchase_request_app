from api.services.socketio_server.sio_instance import sio
from loguru import logger
from typing import Any, Dict, Optional, Union
from api.schemas.ldap_schema import LDAPUser
from api.services.socketio_server.socket_state import user_sids, sid_user as sid_user_map
from fastapi import Depends
from api.dependencies.pras_dependencies import auth_service
from api.utils.misc_utils import format_username

async def decode_and_validate_token(token: str) -> LDAPUser:
    return await auth_service.get_current_user(token)

# Extract sid helper function - removed duplicate definition

# SocketIO events
@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    if not token:
        return False
    
    # verify the token
    user = await decode_and_validate_token(token)
    if not user:
        return False
    
    # Map username -> sid
    user_sids.setdefault(user.username, set()).add(sid)
    sid_user_map[sid] = user.username
    logger.debug(f"socketio: connect {sid} {user.username}")
    
    return sid_user_map

@sio.event
async def progress_update(sid: str, payload: Dict[str, Any]) -> None:
    await sio.emit("PROGRESS_UPDATE", payload, to=sid)

@sio.event
async def start_toast(sid: str, percent: int = 0) -> None:
    await sio.emit("START_TOAST", {"percent_complete": percent}, to=sid)

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
    
@sio.event
async def ping_from_client(sid, data):
    await sio.emit("pong_from_server", {"got": data}, to=sid)

@sio.event
async def connection_timeout(sid):
    logger.debug(f"socketio: connection_timeout {sid}")
    await sio.emit("CONNECTION_TIMEOUT", {"message": "Connection timed out. Reconnecting..."}, to=sid)
    
@sio.on("reset_data")
async def reset_data(sid):
    logger.debug("socketio: reset_data", sid)
    

    
@sio.on("NO_USER_FOUND")
async def no_user_found(sid, data):
    logger.debug("socketio: no_user_found", sid)
    
@sio.on("USER_FOUND")
async def user_found(sid, data):
    logger.debug("socketio: user_found", sid)
    
@sio.on("SIGNAL_RESET")
async def signal_reset(sid, data):
    logger.debug("socketio: signal_reset", sid)
    
@sio.on("EMAIL_SENT")
async def email_sent(sid, data):
    logger.debug(f"Email sent, progress is complete if approval === PENDING: {sid}: {data}")
