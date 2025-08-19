from typing import List
import json
import asyncio
from loguru import logger
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._heartbeat_task: asyncio.Task | None = None
        self._stop = asyncio.Event()

	#-------------------------------------------------------------
	# START HEARTBEAT
	#-------------------------------------------------------------
    async def start(self):
        """Start heartbeat to keep connections alive"""
        if not self._heartbeat_task:
            self._stop.clear()
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

	#-------------------------------------------------------------
	# STOP HEARTBEAT
	#-------------------------------------------------------------
    async def stop(self):
        self._stop.set()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

	#-------------------------------------------------------------
	# HEARTBEAT LOOP
	#-------------------------------------------------------------
    async def _heartbeat_loop(self):
        """Send heartbeat every 30 seconds to keep connections alive"""
        while not self._stop.is_set():
            try:
                await asyncio.sleep(25)
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
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to connection: {e}")
                dead.append(ws)
        
        # Remove dead connections
        for ws in dead:
            await self.disconnect(ws)
 
	#-------------------------------------------------------------
	# GET CONNECTION COUNT
	#-------------------------------------------------------------
    def get_connection_count(self) -> int:
        return len(self.active_connections)
        
websock_conn = ConnectionManager()