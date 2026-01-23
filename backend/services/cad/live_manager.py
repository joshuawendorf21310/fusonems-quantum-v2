import asyncio
from typing import Any, Dict, Set

from fastapi import WebSocket

from utils.logger import logger


class CadLiveManager:
    def __init__(self) -> None:
        self._connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, org_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(org_id, set()).add(websocket)
        logger.info("CAD live websocket connected for org %s", org_id)

    async def disconnect(self, org_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            if org_id in self._connections:
                self._connections[org_id].discard(websocket)
                if not self._connections[org_id]:
                    self._connections.pop(org_id, None)
        logger.info("CAD live websocket disconnected for org %s", org_id)

    async def broadcast(self, org_id: int, payload: Dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._connections.get(org_id, set()))
        if not sockets:
            return
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except Exception as exc:
                logger.warning("CAD live websocket send failed: %s", exc)
                await self.disconnect(org_id, socket)


cad_live_manager = CadLiveManager()
