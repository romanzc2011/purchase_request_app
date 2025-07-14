from typing import List
import json
from fastapi import WebSocket
from api.schemas.enums import PRProgress

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

	#-------------------------------------------------------------
	# CONNECT
	#-------------------------------------------------------------
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

	#-------------------------------------------------------------
	# DISCONNECT
	#-------------------------------------------------------------
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

	#-------------------------------------------------------------
	# BROADCAST
	#-------------------------------------------------------------
    async def broadcast(self, message: PRProgress):
        """
        This will also handle how much work has been completed
        total_steps = 10
        completed_steps = 5
        percent = (completed_steps / total_steps) * 100
        message = {
            "status": "in_progress",
            "percent": percent
        }
        """
        disconnected = []
        for connection in self.active_connections:
            
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for connection in disconnected:
            await self.disconnect(connection)

	#-------------------------------------------------------------
	# BROADCAST BOOLEAN
	#-------------------------------------------------------------
    async def broadcast_boolean(self, value: bool):
        await self.broadcast(json.dumps({"boolean": value}))
        
    