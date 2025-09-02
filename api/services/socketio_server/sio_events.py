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