# Socket.IO setup
import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["http://localhost:5004", "http://localhost:5002"],
    ping_timeout=20,
    ping_interval=25
)