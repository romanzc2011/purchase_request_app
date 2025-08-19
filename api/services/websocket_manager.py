from contextlib import suppress
from typing import List
import json
import asyncio
from loguru import logger
from fastapi import WebSocket
import socket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._task: asyncio.Task | None = None
        self.server_address = (socket.gethostbyname(socket.gethostname()), 5004)
    
    #-------------------------------------------------------------
    # START
    #-------------------------------------------------------------
    async def start(self):
        if not self._task:
            self._task = asyncio.create_task(self.start_heartbeat())
            
    #-------------------------------------------------------------
    # STOP
    #-------------------------------------------------------------
    async def stop(self):
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

	#-------------------------------------------------------------
	# START HEARTBEAT
	#-------------------------------------------------------------
    async def start_heartbeat(self):
        reader, writer = await asyncio.open_connection(*self.server_address)
        s = writer.get_extra_info("socket")
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if hasattr(socket, "SIO_KEEPALIVE_VALS"):
            s.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60_000, 30_000))

        try:
            while True:
                line = await reader.readline()   # waits for '\n'
                if not line:
                    break
                logger.debug("HEARTBEAT: {}", line.decode(errors="replace").rstrip())
        finally:
            writer.close()
            await writer.wait_closed()
            
    #-------------------------------------------------------------
    # CONNECT
    #-------------------------------------------------------------
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
        
    #-------------------------------------------------------------
    # DISCONNECT
    #-------------------------------------------------------------
    async def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)
    
    #-------------------------------------------------------------
    # BROADCAST
    #-------------------------------------------------------------
    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
                logger.debug(message)
            except Exception as e:
                logger.warning(f"Failed to send message to connection: {e}")
                dead.append(ws)
        
        # Remove disconnected connections
        for ws in dead:
            await self.disconnect(ws)

        
    #     """Start heartbeat to keep connections alive"""
    #     if self.heartbeat_task is None:
    #         self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    # async def _heartbeat_loop(self):
    #     """Send heartbeat every 30 seconds to keep connections alive"""
    #     while True:
    #         try:
    #             await asyncio.sleep(30)  # Send heartbeat every 30 seconds
    #             if self.active_connections:
    #                 await self.broadcast({"event": "heartbeat", "timestamp": asyncio.get_event_loop().time()})
    #                 logger.debug(f"Sent heartbeat to {len(self.active_connections)} connections")
    #         except Exception as e:
    #             logger.error(f"Heartbeat error: {e}")

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
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.debug(message)
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