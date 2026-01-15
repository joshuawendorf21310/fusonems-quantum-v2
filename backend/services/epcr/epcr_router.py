from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.epcr import Patient
from models.user import UserRole


router = APIRouter(prefix="/api/epcr", tags=["ePCR"])


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    incident_number: str
    vitals: dict = {}
    interventions: list = []
    medications: list = []
    procedures: list = []


class PatientResponse(PatientCreate):
    id: int

    class Config:
        from_attributes = True


@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    patient = Patient(**payload.dict())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("/patients", response_model=list[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).order_by(Patient.created_at.desc()).all()
