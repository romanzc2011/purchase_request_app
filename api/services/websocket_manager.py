from typing import List
import json
import asyncio
from loguru import logger
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.heartbeat_task = None
        # Don't start heartbeat during initialization - it will be started when needed

	#-------------------------------------------------------------
	# START HEARTBEAT
	#-------------------------------------------------------------
    def start_heartbeat(self):
        """Start heartbeat to keep connections alive"""
        if self.heartbeat_task is None:
            try:
                # Only create task if there's a running event loop
                loop = asyncio.get_running_loop()
                self.heartbeat_task = loop.create_task(self._heartbeat_loop())
            except RuntimeError:
                # No running event loop, heartbeat will be started when needed
                logger.debug("No running event loop, heartbeat will be started later")
                pass

    async def _heartbeat_loop(self):
        """Send heartbeat every 30 seconds to keep connections alive"""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                if self.active_connections:
                    await self.broadcast({"event": "heartbeat", "timestamp": asyncio.get_event_loop().time()})
                    logger.debug(f"Sent heartbeat to {len(self.active_connections)} connections")
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

	#-------------------------------------------------------------
	# CONNECT
	#-------------------------------------------------------------
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Start heartbeat when first connection is made
        if self.heartbeat_task is None:
            self.start_heartbeat()

	#-------------------------------------------------------------
	# DISCONNECT
	#-------------------------------------------------------------
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

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