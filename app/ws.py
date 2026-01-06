# backend/ws.py
import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: Dict[str, Any]):
        payload = json.dumps(message)
        # copy connections under lock, but send outside lock
        async with self._lock:
            conns = list(self.active_connections)
        for connection in conns:
            try:
                await connection.send_text(payload)
            except Exception:
                # best-effort removal of dead connection
                try:
                    await self.disconnect(connection)
                except Exception:
                    pass

# single manager instance used across app
manager = ConnectionManager()
