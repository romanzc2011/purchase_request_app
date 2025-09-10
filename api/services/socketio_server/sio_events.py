from api.services.socketio_server.sio_instance import sio
from loguru import logger
from typing import Any, Dict
from api.services.auth_service import AuthService
from api.services.ldap_service import LDAPService
from api.schemas.ldap_schema import LDAPUser
from api.settings import settings
from api.services.socketio_server.socket_state import user_sids, sid_user as sid_user_map
from fastapi import Depends

# Create auth service instance locally to prevent the circular import issue
ldap_service = LDAPService(
    ldap_url=settings.ldap_server,
    bind_dn=settings.ldap_service_user,
    bind_password=settings.ldap_service_password,
    group_dns=[
        settings.it_group_dns,
        settings.cue_group_dns,
        settings.access_group_dns,
    ],
)
auth_service = AuthService(ldap_service=ldap_service)

async def decode_and_validate_token(token: str) -> LDAPUser:
    return await auth_service.get_current_user(token)

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

def get_user_sid(current_user) -> str | None:
    """
    Get the SocketIO session ID for the current user.
    Returns None if no session is found.
    """
    from api.services.socketio_server.socket_state import user_sids
    user_sid_set = user_sids.get(current_user.username, set())
    if not user_sid_set:
        logger.warning(f"No SocketIO session found for user {current_user.username}")
        return None
    else:
        # Use the first available session ID
        return next(iter(user_sid_set))
    
    
@sio.event
async def disconnect(sid):
    logger.debug("socketio: disconnect ", sid)
    
@sio.event
async def ping_from_client(sid, data):
    await sio.emit("pong_from_server", {"got": data}, to=sid)
    
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
