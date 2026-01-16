from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.event import EventLog
from models.user import User, UserRole
from utils.events import event_bus
from utils.tenancy import scoped_query
from utils.time import compute_drift_seconds, parse_device_time, utc_now
from utils.classification import normalize_classification
from utils.write_ops import audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/events",
    tags=["Event Bus"],
    dependencies=[Depends(require_module("EVENTS"))],
)


class EventCreate(BaseModel):
    event_type: str
    payload: dict
    idempotency_key: Optional[str] = None


class ReplayRequest(BaseModel):
    event_types: Optional[list[str]] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def publish_event(
    payload: EventCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    server_time = utc_now()
    device_time = parse_device_time(payload.payload.get("device_time"))
    drift_seconds, drifted = compute_drift_seconds(device_time, server_time)
    record = event_bus.publish(
        db=db,
        org_id=user.org_id,
        event_type=payload.event_type,
        payload=payload.payload,
        actor_id=user.id,
        actor_role=user.role,
        idempotency_key=payload.idempotency_key,
        device_id=payload.payload.get("device_id", ""),
        server_time=server_time,
        drift_seconds=drift_seconds,
        drifted=drifted,
        training_mode=request.state.training_mode,
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="event_log",
        classification=normalize_classification(payload.payload.get("classification", "OPS")),
        after_state=model_snapshot(record),
        event_type="events.published",
    )
    return record


@router.get("")
def list_events(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, EventLog, user.org_id, request.state.training_mode).order_by(
        EventLog.created_at.desc()
    ).all()


@router.post("/replay")
def replay_events(
    payload: ReplayRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    results = event_bus.replay(
        db=db,
        org_id=user.org_id,
        event_types=payload.event_types,
        training_mode=request.state.training_mode,
    )
    return {"status": "replayed", "count": len(results), "results": results}
