import json
from typing import Dict

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import get_current_user, require_roles
from models.user import User, UserRole
from utils.logger import logger
from utils.write_ops import audit_and_event

router = APIRouter(
    prefix="/api/cad",
    tags=["Tracking"],
    dependencies=[Depends(require_module("CAD"))],
)

# Active units dictionary keyed by org_id
active_units: Dict[int, Dict[str, dict]] = {}

# --- GPS Update via POST (for units or MDTs) ---
@router.post("/track")
async def update_position(
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.dispatcher, UserRole.provider)),
):
    unit_id = data.get("unit_id")
    lat = data.get("lat")
    lon = data.get("lon")

    if not all([unit_id, lat, lon]):
        return {"error": "Missing unit_id, lat, or lon"}

    org_units = active_units.setdefault(user.org_id, {})
    org_units[unit_id] = {"lat": lat, "lon": lon}
    logger.info("Updated position for %s: (%s, %s)", unit_id, lat, lon)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_tracking",
        classification="OPS",
        after_state={"unit_id": unit_id, "lat": lat, "lon": lon},
        event_type="cad.tracking.updated",
        event_payload={"unit_id": unit_id, "lat": lat, "lon": lon},
    )
    return {"status": "ok", "unit_id": unit_id, "lat": lat, "lon": lon}

@router.get("/track")
async def list_positions(user: User = Depends(get_current_user)):
    return active_units.get(user.org_id, {})


# --- Live WebSocket updates for Dispatchers ---
@router.websocket("/ws/track")
async def tracking_websocket(websocket: WebSocket, user: User = Depends(get_current_user)):
    await websocket.accept()
    logger.info("Dispatcher connected to tracking WebSocket.")
    try:
        while True:
            data = json.dumps(active_units.get(user.org_id, {}))
            await websocket.send_text(data)
    except WebSocketDisconnect:
        logger.info("Dispatcher disconnected from tracking WebSocket.")
