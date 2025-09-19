# Socket.IO setup
import socketio
import asyncio

allowed = [
    "https://10.234.198.113:5002",   # IIS TLS origin you’re using
    "https://LAWB-SHCOL-7920.adu.dcn",  # if you use the CN/hostname
    "http://localhost:5002", "http://127.0.0.1:5002",  # for dev
]
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    transports=["polling", "websocket"],
    logger=True,
    engineio_logger=True,
    ping_interval=25,
    ping_timeout=60,
    max_http_buffer_size=1_000_000,
    allow_upgrades=True,
)
socketio_app = socketio.ASGIApp(sio, socketio_path="communicate")

# Debug: Print SocketIO configuration
print(f"SocketIO configured with path: /progress_bar_bridge/communicate")
print(f"SocketIO transports: {sio.transport}")

# Remember server loop so worker threads can schedule emits on it
_server_loop: asyncio.AbstractEventLoop | None = None

def set_server_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _server_loop
    _server_loop = loop
    
def get_server_loop() -> asyncio.AbstractEventLoop:
    return _server_loop

def emit_async(event: str, data: dict, to: str | None = None) -> None:
    # Fire and forget
    async def _emit():
        await sio.emit(event, data, to=to)
        
    try:
        loop = get_server_loop()
        loop.create_task(_emit())
    except RuntimeError:
        loop = get_server_loop()
        if loop is None:
            raise RuntimeError("Server loop not set; call set_server_loop() at startup")
        asyncio.run_coroutine_threadsafe(_emit(), loop)