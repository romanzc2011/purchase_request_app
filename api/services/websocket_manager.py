from contextlib import suppress
from typing import List
import json
import asyncio
from loguru import logger
from fastapi import WebSocket
import socket
from contextlib import suppress

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._hb_task: asyncio.Task | None = None
    
    #-------------------------------------------------------------
    # START
    #-------------------------------------------------------------
    async def start(self):
        if not self._hb_task:
            self._hb_task = asyncio.create_task(self._heartbeat())
            
    #-------------------------------------------------------------
    # STOP
    #-------------------------------------------------------------
    async def stop(self):
        if self._hb_task:
            self._hb_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._hb_task
            self._hb_task = None

    #-------------------------------------------------------------
    # HEARTBEAT
    #-------------------------------------------------------------
    async def _heartbeat(self):
        while True:
            await asyncio.sleep(25)
            if self.active_connections:
                await self.broadcast({"event": "srv_heartbeat"})
            
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
        
	#-------------------------------------------------------------
	# GET CONNECTION COUNT
	#-------------------------------------------------------------
    def get_connection_count(self) -> int:
        return len(self.active_connections)
        
websock_conn = ConnectionManager()