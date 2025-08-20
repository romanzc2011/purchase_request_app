from typing import List
import json
import asyncio
from loguru import logger
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

	#-------------------------------------------------------------
	# CONNECT
	#-------------------------------------------------------------
    async def accept_connections(self, websocket: WebSocket):
        logger.info("🔌 ConnectionManager: Accepting WebSocket connection")
        # Accept the connection
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ ConnectionManager: WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial message to client to let them know they are connected
        await websocket.send_json({
            "event": "connection_status",
            "connected": True,
            "timestamp": asyncio.get_event_loop().time(),
        })
        
    async def filter_events(self, websocket: WebSocket, incoming_data: str):
        # Convert to json, if reset_data then reset shm, percent everything
            try:
                message = json.loads(incoming_data)
                if message.get("event") == "reset_data":
                    # reset shm
                    logger.info(f"Progress state cleared via WebSocket reset")
                elif message.get("event") == "check_connection":
                    # Send connection status back
                    await websocket.send_json({
                        "event": "connection_status",
                        "connected": True,
                        "timestamp": asyncio.get_event_loop().time(),
                    })
                    logger.info(f"📤 Sent connection_status")
                elif message.get("event") == "clear_stale_state":
                    # Clear stale progress state
                    await websocket.send_json({
                        "event": "state_cleared",
                        "timestamp": asyncio.get_event_loop().time(),
                    })
                    logger.info(f"📤 Sent state_cleared")
                elif message.get("event") == "ping":
                    # Handle ping/pong for keep-alive
                    await websocket.send_json({
                        "event": "pong",
                        "timestamp": asyncio.get_event_loop().time(),
                    })
                    logger.info(f"📤 Sent pong")
                elif message.get("event") == "client_test":
                    # Handle client test message
                    await websocket.send_json({
                        "event": "server_response",
                        "message": "Hello client! Server received your test message.",
                        "timestamp": asyncio.get_event_loop().time(),
                    })
                    logger.info(f"📤 Sent server response")
            except json.JSONDecodeError:
                logger.error(f"Received non-JSON data: {incoming_data}")

	#-------------------------------------------------------------
	# DISCONNECT
	#-------------------------------------------------------------
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"❌ ConnectionManager: WebSocket disconnected. Total connections: {len(self.active_connections)}")
        else:
            logger.warning("❌ ConnectionManager: Attempted to disconnect WebSocket that wasn't in active connections")

	#-------------------------------------------------------------
	# BROADCAST
	#-------------------------------------------------------------
    async def broadcast(self, message: dict):
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
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)
                
	#-------------------------------------------------------------
	# BROADCAST BOOLEAN
	#-------------------------------------------------------------
    async def broadcast_boolean(self, value: bool):
        await self.broadcast(json.dumps({"boolean": value}))
        
	#-------------------------------------------------------------
	# GET CONNECTION COUNT
	#-------------------------------------------------------------
    def get_connection_count(self) -> int:
        return len(self.active_connections)
        
websock_conn = ConnectionManager()