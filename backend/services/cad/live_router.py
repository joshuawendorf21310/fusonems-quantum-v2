from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from core.guards import require_module
from core.security import get_current_user
from models.user import User
from services.cad.live_manager import cad_live_manager
from utils.logger import logger

router = APIRouter(
    prefix="/api/cad",
    tags=["CAD"],
    dependencies=[Depends(require_module("CAD"))],
)


@router.websocket("/live")
async def cad_live_websocket(websocket: WebSocket, user: User = Depends(get_current_user)):
    await cad_live_manager.connect(user.org_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("CAD live websocket disconnected")
    finally:
        await cad_live_manager.disconnect(user.org_id, websocket)
