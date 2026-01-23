from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.scheduling import Shift
from models.user import User, UserRole
from utils.tenancy import get_scoped_record, scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


router = APIRouter(
    prefix="/api/schedule",
    tags=["Scheduling"],
    dependencies=[Depends(require_module("SCHEDULING"))],
)


class ShiftCreate(BaseModel):
    crew_name: str
    shift_start: datetime
    shift_end: datetime
    status: str = "Scheduled"
    certifications: list = []


class ShiftResponse(ShiftCreate):
    id: int

    class Config:
        from_attributes = True


@router.post("/shifts", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: ShiftCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    shift = Shift(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(shift, request)
    db.add(shift)
    db.commit()
    db.refresh(shift)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="schedule_shift",
        classification=shift.classification,
        after_state=model_snapshot(shift),
        event_type="schedule.shift.created",
        event_payload={"shift_id": shift.id},
    )
    return shift


@router.get("/shifts", response_model=list[ShiftResponse])
def list_shifts(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, Shift, user.org_id, request.state.training_mode).order_by(
        Shift.shift_start.asc()
    ).all()


@router.post("/shifts/{shift_id}/swap")
def swap_shift(
    shift_id: int,
    new_crew: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    shift = get_scoped_record(db, request, Shift, shift_id, user, resource_label="schedule")
    before = model_snapshot(shift)
    shift.crew_name = new_crew
    shift.status = "Swapped"
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="schedule_shift",
        classification=shift.classification,
        before_state=before,
        after_state=model_snapshot(shift),
        event_type="schedule.shift.updated",
        event_payload={"shift_id": shift.id},
    )
    return {"status": "ok", "shift_id": shift.id, "crew_name": shift.crew_name}


@router.get("/alerts")
def scheduling_alerts():
    return {
        "overtime": ["Unit A1 approaching overtime threshold"],
        "shortages": ["Night shift requires 1 paramedic"],
        "certifications": ["Crew B missing ACLS recertification"],
    }
