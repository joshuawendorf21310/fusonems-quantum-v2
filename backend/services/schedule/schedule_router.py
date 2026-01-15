from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.scheduling import Shift
from models.user import UserRole


router = APIRouter(prefix="/api/schedule", tags=["Scheduling"])


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
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    shift = Shift(**payload.dict())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.get("/shifts", response_model=list[ShiftResponse])
def list_shifts(db: Session = Depends(get_db)):
    return db.query(Shift).order_by(Shift.shift_start.asc()).all()


@router.post("/shifts/{shift_id}/swap")
def swap_shift(
    shift_id: int,
    new_crew: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    shift.crew_name = new_crew
    shift.status = "Swapped"
    db.commit()
    return {"status": "ok", "shift_id": shift.id, "crew_name": shift.crew_name}


@router.get("/alerts")
def scheduling_alerts():
    return {
        "overtime": ["Unit A1 approaching overtime threshold"],
        "shortages": ["Night shift requires 1 paramedic"],
        "certifications": ["Crew B missing ACLS recertification"],
    }
