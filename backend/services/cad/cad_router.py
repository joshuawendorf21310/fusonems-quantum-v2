from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.cad import Call, Dispatch, Unit
from models.user import UserRole
from utils.logger import logger

router = APIRouter(prefix="/api/cad", tags=["CAD"])


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


@router.post("/calls", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
def create_call(
    payload: CallCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = Call(**payload.dict())
    db.add(call)
    db.commit()
    db.refresh(call)
    logger.info("Call logged %s", call.id)
    return call


@router.get("/calls", response_model=list[CallResponse])
def list_calls(db: Session = Depends(get_db)):
    return db.query(Call).order_by(Call.created_at.desc()).all()


@router.get("/units")
def get_units(db: Session = Depends(get_db)):
    units = db.query(Unit).order_by(Unit.unit_identifier.asc()).all()
    return {"active_units": units}


@router.post("/units", status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: UnitCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    unit = Unit(**payload.dict())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


@router.post("/dispatch")
def dispatch_unit(
    payload: DispatchRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = db.query(Call).filter(Call.id == payload.call_id).first()
    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    unit = db.query(Unit).filter(Unit.unit_identifier == payload.unit_identifier).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    distance_km = _haversine(call.latitude, call.longitude, unit.latitude, unit.longitude)
    eta_minutes = _estimate_eta(distance_km)
    call.eta_minutes = eta_minutes
    call.status = "Dispatched"
    unit.status = "En Route"
    dispatch = Dispatch(call_id=call.id, unit_id=unit.id, status="Dispatched")
    db.add(dispatch)
    db.commit()
    logger.info("Dispatching %s to call %s", unit.unit_identifier, call.id)
    return {"status": "dispatched", "eta_minutes": eta_minutes}
