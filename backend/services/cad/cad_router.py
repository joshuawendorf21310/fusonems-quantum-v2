from math import asin, cos, radians, sin, sqrt

import anyio

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.cad import Call, Dispatch, Unit
from models.user import User, UserRole
from services.cad.live_manager import cad_live_manager
from utils.logger import logger
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from utils.tenancy import get_scoped_record, scoped_query

router = APIRouter(
    prefix="/api/cad",
    tags=["CAD"],
    dependencies=[Depends(require_module("CAD"))],
)


class CallCreate(BaseModel):
    caller_name: str
    caller_phone: str
    location_address: str
    latitude: float
    longitude: float
    priority: str = "Routine"


class CallResponse(BaseModel):
    id: int
    caller_name: str
    caller_phone: str
    location_address: str
    latitude: float
    longitude: float
    priority: str
    status: str
    eta_minutes: int | None

    class Config:
        from_attributes = True


class UnitCreate(BaseModel):
    unit_identifier: str
    status: str = "Available"
    latitude: float = 0.0
    longitude: float = 0.0


class DispatchRequest(BaseModel):
    call_id: int
    unit_identifier: str


class AssignRequest(BaseModel):
    unit_identifier: str


class StatusUpdate(BaseModel):
    status: str
    unit_identifier: str | None = None


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(
        dlon / 2
    ) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _estimate_eta(distance_km: float, speed_kph: float = 60.0) -> int:
    if speed_kph <= 0:
        return 0
    return max(1, int((distance_km / speed_kph) * 60))


def _broadcast_update(org_id: int, payload: dict) -> None:
    try:
        anyio.from_thread.run(cad_live_manager.broadcast, org_id, payload)
    except RuntimeError:
        logger.info("CAD live broadcast skipped: no event loop")


def _set_unit_status(unit: Unit, status: str) -> None:
    status_map = {
        "Enroute": "En Route",
        "OnScene": "On Scene",
        "Transport": "Transporting",
        "Available": "Available",
        "Dispatched": "En Route",
    }
    unit.status = status_map.get(status, status)


@router.post("/calls", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
def create_call(
    payload: CallCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = Call(**payload.dict(), org_id=user.org_id)
    apply_training_mode(call, request)
    db.add(call)
    db.commit()
    db.refresh(call)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="cad_call",
        classification=call.classification,
        after_state=model_snapshot(call),
        event_type="cad.call.created",
        event_payload={"call_id": call.id, "priority": call.priority},
    )
    logger.info("Call logged %s", call.id)
    _broadcast_update(
        user.org_id,
        {"event": "cad.call.created", "call_id": call.id, "priority": call.priority},
    )
    return call


@router.get("/calls", response_model=list[CallResponse])
def list_calls(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, Call, user.org_id, request.state.training_mode).order_by(
        Call.created_at.desc()
    ).all()


@router.get("/units")
def get_units(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    units = scoped_query(db, Unit, user.org_id, request.state.training_mode).order_by(
        Unit.unit_identifier.asc()
    ).all()
    return {"active_units": units}


@router.post("/units", status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: UnitCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    unit = Unit(**payload.dict(), org_id=user.org_id)
    apply_training_mode(unit, request)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="cad_unit",
        classification=unit.classification,
        after_state=model_snapshot(unit),
        event_type="cad.unit.created",
        event_payload={"unit_identifier": unit.unit_identifier},
    )
    _broadcast_update(
        user.org_id,
        {"event": "cad.unit.created", "unit_identifier": unit.unit_identifier},
    )
    return unit


def _dispatch_to_unit(
    *,
    call: Call,
    unit: Unit,
    request: Request,
    db: Session,
    user: User,
) -> dict:
    call_before = model_snapshot(call)
    unit_before = model_snapshot(unit)
    distance_km = _haversine(call.latitude, call.longitude, unit.latitude, unit.longitude)
    eta_minutes = _estimate_eta(distance_km)
    call.eta_minutes = eta_minutes
    call.status = "Dispatched"
    _set_unit_status(unit, "Dispatched")
    dispatch = Dispatch(call_id=call.id, unit_id=unit.id, status="Dispatched", org_id=user.org_id)
    apply_training_mode(dispatch, request)
    db.add(dispatch)
    db.commit()
    db.refresh(dispatch)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_call",
        classification=call.classification,
        before_state=call_before,
        after_state=model_snapshot(call),
        event_type="cad.call.dispatched",
        event_payload={"call_id": call.id, "unit_identifier": unit.unit_identifier},
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_unit",
        classification=unit.classification,
        before_state=unit_before,
        after_state=model_snapshot(unit),
        event_type="cad.unit.dispatched",
        event_payload={"call_id": call.id, "status": call.status},
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="cad_dispatch",
        classification=dispatch.classification,
        after_state=model_snapshot(dispatch),
        event_type="cad.dispatch.created",
        event_payload={"dispatch_id": dispatch.id, "call_id": call.id},
    )
    _broadcast_update(
        user.org_id,
        {
            "event": "cad.dispatch.created",
            "call_id": call.id,
            "unit_identifier": unit.unit_identifier,
        },
    )
    logger.info("Dispatching %s to call %s", unit.unit_identifier, call.id)
    return {"status": "dispatched", "eta_minutes": eta_minutes}


@router.post("/dispatch")
def dispatch_unit(
    payload: DispatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = get_scoped_record(db, request, Call, payload.call_id, user)
    unit = scoped_query(db, Unit, user.org_id, request.state.training_mode).filter(
        Unit.unit_identifier == payload.unit_identifier
    ).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return _dispatch_to_unit(call=call, unit=unit, request=request, db=db, user=user)


@router.post("/calls/{call_id}/assign")
def assign_unit(
    call_id: int,
    payload: AssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = get_scoped_record(db, request, Call, call_id, user)
    unit = scoped_query(db, Unit, user.org_id, request.state.training_mode).filter(
        Unit.unit_identifier == payload.unit_identifier
    ).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return _dispatch_to_unit(call=call, unit=unit, request=request, db=db, user=user)


@router.patch("/calls/{call_id}/status")
def update_call_status(
    call_id: int,
    payload: StatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = get_scoped_record(db, request, Call, call_id, user)
    call_before = model_snapshot(call)
    call.status = payload.status
    unit_before = None
    unit = None
    if payload.unit_identifier:
        unit = scoped_query(db, Unit, user.org_id, request.state.training_mode).filter(
            Unit.unit_identifier == payload.unit_identifier
        ).first()
        if not unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
        unit_before = model_snapshot(unit)
        _set_unit_status(unit, payload.status)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_call",
        classification=call.classification,
        before_state=call_before,
        after_state=model_snapshot(call),
        event_type="cad.call.status.updated",
        event_payload={"call_id": call.id, "status": call.status},
    )
    if unit and unit_before is not None:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="update",
            resource="cad_unit",
            classification=unit.classification,
            before_state=unit_before,
            after_state=model_snapshot(unit),
            event_type="cad.unit.status.updated",
            event_payload={"unit_identifier": unit.unit_identifier, "status": unit.status},
        )
    _broadcast_update(
        user.org_id,
        {"event": "cad.call.status.updated", "call_id": call.id, "status": call.status},
    )
    return {"status": "ok", "call_id": call.id, "call_status": call.status}
