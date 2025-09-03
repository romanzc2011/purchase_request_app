from api.services.socketio_server.sio_instance import sio
from loguru import logger

# SocketIO events
@sio.event
async def connect(sid, environ):
    logger.debug("socketio: connect", sid)
    
@sio.event
async def disconnect(sid):
    logger.debug("socketio: disconnect ", sid)
    
@sio.event
async def ping_from_client(sid, data):
    await sio.emit("pong_from_server", {"got": data}, to=sid)
    
@sio.on("reset_data")
async def reset_data(sid):
    logger.debug("socketio: reset_data", sid)
    
@sio.on("PROGRESS_UPDATE")
async def progress_update(sid, data):
    logger.debug("socketio: progress_update", sid)
    
@sio.on("START_TOAST")
async def start_toast(sid, data):
    logger.debug("socketio: start_toast", sid)

@sio.on("NO_USER_FOUND")
async def no_user_found(sid, data):
    logger.debug("socketio: no_user_found", sid)
    
@sio.on("USER_FOUND")
async def user_found(sid, data):
    logger.debug("socketio: user_found", sid)
    
@sio.on("SIGNAL_RESET")
async def signal_reset(sid, data):
    logger.debug("socketio: signal_reset", sid)
