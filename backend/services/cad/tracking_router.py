from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils.logger import logger
from typing import Dict
import json

router = APIRouter(prefix="/api/cad", tags=["Tracking"])

# Active units dictionary
active_units: Dict[str, dict] = {}

# --- GPS Update via POST (for units or MDTs) ---
@router.post("/track")
async def update_position(data: dict):
    unit_id = data.get("unit_id")
    lat = data.get("lat")
    lon = data.get("lon")

    if not all([unit_id, lat, lon]):
        return {"error": "Missing unit_id, lat, or lon"}

    active_units[unit_id] = {"lat": lat, "lon": lon}
    logger.info(f"Updated position for {unit_id}: ({lat}, {lon})")
    return {"status": "ok", "unit_id": unit_id, "lat": lat, "lon": lon}


# --- Live WebSocket updates for Dispatchers ---
@router.websocket("/ws/track")
async def tracking_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("Dispatcher connected to tracking WebSocket.")
    try:
        while True:
            data = json.dumps(active_units)
            await websocket.send_text(data)
    except WebSocketDisconnect:
        logger.info("Dispatcher disconnected from tracking WebSocket.")
