# Socket.IO setup
import socketio

allowed = [
    "https://10.234.198.113:5002",   # IIS TLS origin you’re using
    "https://LAWB-SHCOL-7920.adu.dcn",  # if you use the CN/hostname
    "http://localhost:5002", "http://127.0.0.1:5002",  # for dev
]
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    transports=["polling"],
    logger=True,
    engineio_logger=True,
    ping_interval=25,
    ping_timeout=60,
    max_http_buffer_size=1_000_000,
)