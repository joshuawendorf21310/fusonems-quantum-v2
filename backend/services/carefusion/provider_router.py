from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_telehealth_db
from core.security import require_roles
from models.telehealth import (
    TelehealthProvider,
    TelehealthPatient,
    TelehealthAppointment,
    TelehealthVisit,
    ProviderAvailability,
    TelehealthPrescription,
)
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(prefix="/api/carefusion/provider", tags=["CareFusion Provider"])


class ProviderRegistration(BaseModel):
    name: str
    specialty: str = ""
    credentials: str = ""
    license_number: str = ""
    license_state: str = ""
    email: str
    phone: str = ""
    bio: str = ""
    accepts_new_patients: bool = True


class AvailabilityCreate(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int = 30
    override_date: Optional[datetime] = None


class VisitCreate(BaseModel):
    appointment_id: str
    patient_id: str
    chief_complaint: str
    history_of_present_illness: str = ""
    vital_signs: str = ""
    physical_exam: str = ""
    assessment: str = ""
    diagnosis_codes: str = ""
    treatment_plan: str = ""
    prescriptions_issued: str = ""
    follow_up_instructions: str = ""


class VisitUpdate(BaseModel):
    history_of_present_illness: Optional[str] = None
    vital_signs: Optional[str] = None
    physical_exam: Optional[str] = None
    assessment: Optional[str] = None
    diagnosis_codes: Optional[str] = None
    treatment_plan: Optional[str] = None
    prescriptions_issued: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    billing_code: Optional[str] = None
    billing_amount: Optional[Decimal] = None
    status: Optional[str] = None


class PrescriptionCreate(BaseModel):
    visit_id: str
    patient_id: str
    medication_name: str
    dosage: str
    quantity: str
    refills: int = 0
    directions: str
    pharmacy_name: str = ""
    pharmacy_phone: str = ""
    pharmacy_fax: str = ""


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_provider(
    payload: ProviderRegistration,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    import uuid
    provider_id = f"PRV-{uuid.uuid4().hex[:12].upper()}"
    
    provider = TelehealthProvider(
        org_id=user.org_id,
        provider_id=provider_id,
        user_id=user.id,
        **payload.model_dump(),
    )
    apply_training_mode(provider, request)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="telehealth_provider",
        classification="PHI",
        after_state=model_snapshot(provider),
        event_type="carefusion.provider.registered",
        event_payload={"provider_id": provider.id},
    )
    return model_snapshot(provider)


@router.get("/profile/{provider_id}")
def get_provider_profile(
    provider_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    provider = (
        scoped_query(db, TelehealthProvider, user.org_id, request.state.training_mode)
        .filter(TelehealthProvider.provider_id == provider_id)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return model_snapshot(provider)


@router.get("/patients")
def list_provider_patients(
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    patients = (
        scoped_query(db, TelehealthPatient, user.org_id, request.state.training_mode)
        .filter(TelehealthPatient.status == "active")
        .order_by(TelehealthPatient.name)
        .all()
    )
    return [model_snapshot(patient) for patient in patients]


@router.get("/patients/{patient_id}")
def get_patient_detail(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    patient = (
        scoped_query(db, TelehealthPatient, user.org_id, request.state.training_mode)
        .filter(TelehealthPatient.patient_id == patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return model_snapshot(patient)


@router.post("/availability", status_code=status.HTTP_201_CREATED)
def create_availability(
    payload: AvailabilityCreate,
    provider_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    provider = (
        scoped_query(db, TelehealthProvider, user.org_id, request.state.training_mode)
        .filter(TelehealthProvider.provider_id == provider_id)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    
    availability = ProviderAvailability(
        org_id=user.org_id,
        provider_id=provider_id,
        **payload.model_dump(),
    )
    apply_training_mode(availability, request)
    db.add(availability)
    db.commit()
    db.refresh(availability)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="provider_availability",
        classification="PHI",
        after_state=model_snapshot(availability),
        event_type="carefusion.availability.created",
        event_payload={"availability_id": availability.id},
    )
    return model_snapshot(availability)


@router.get("/appointments")
def list_provider_appointments(
    request: Request,
    provider_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, TelehealthAppointment, user.org_id, request.state.training_mode)
    
    if provider_id:
        query = query.filter(TelehealthAppointment.provider_id == provider_id)
    if status_filter:
        query = query.filter(TelehealthAppointment.status == status_filter)
    
    appointments = query.order_by(TelehealthAppointment.scheduled_start.desc()).all()
    return [model_snapshot(apt) for apt in appointments]


@router.put("/appointments/{appointment_id}")
def update_appointment_status(
    appointment_id: str,
    status_update: str,
    provider_notes: str = "",
    request: Request = None,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    appointment = (
        scoped_query(db, TelehealthAppointment, user.org_id, request.state.training_mode)
        .filter(TelehealthAppointment.appointment_id == appointment_id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    
    before_state = model_snapshot(appointment)
    appointment.status = status_update
    appointment.provider_notes = provider_notes
    
    if status_update == "in_progress":
        appointment.actual_start = datetime.utcnow()
    elif status_update == "completed":
        appointment.actual_end = datetime.utcnow()
    
    db.commit()
    db.refresh(appointment)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="telehealth_appointment",
        classification="PHI",
        before_state=before_state,
        after_state=model_snapshot(appointment),
        event_type="carefusion.appointment.updated",
        event_payload={"appointment_id": appointment.id},
    )
    return model_snapshot(appointment)


@router.post("/visits", status_code=status.HTTP_201_CREATED)
def create_visit(
    payload: VisitCreate,
    provider_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    import uuid
    visit_id = f"VST-{uuid.uuid4().hex[:12].upper()}"
    
    visit = TelehealthVisit(
        org_id=user.org_id,
        visit_id=visit_id,
        provider_id=provider_id,
        **payload.model_dump(),
    )
    apply_training_mode(visit, request)
    db.add(visit)
    db.commit()
    db.refresh(visit)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="telehealth_visit",
        classification="PHI",
        after_state=model_snapshot(visit),
        event_type="carefusion.visit.created",
        event_payload={"visit_id": visit.id},
    )
    return model_snapshot(visit)


@router.get("/visits")
def list_provider_visits(
    request: Request,
    provider_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, TelehealthVisit, user.org_id, request.state.training_mode)
    
    if provider_id:
        query = query.filter(TelehealthVisit.provider_id == provider_id)
    if patient_id:
        query = query.filter(TelehealthVisit.patient_id == patient_id)
    
    visits = query.order_by(TelehealthVisit.created_at.desc()).all()
    return [model_snapshot(visit) for visit in visits]


@router.get("/visits/{visit_id}")
def get_visit_detail(
    visit_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    visit = (
        scoped_query(db, TelehealthVisit, user.org_id, request.state.training_mode)
        .filter(TelehealthVisit.visit_id == visit_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return model_snapshot(visit)


@router.put("/visits/{visit_id}")
def update_visit(
    visit_id: str,
    payload: VisitUpdate,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    visit = (
        scoped_query(db, TelehealthVisit, user.org_id, request.state.training_mode)
        .filter(TelehealthVisit.visit_id == visit_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    
    before_state = model_snapshot(visit)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(visit, field, value)
    
    db.commit()
    db.refresh(visit)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="telehealth_visit",
        classification="PHI",
        before_state=before_state,
        after_state=model_snapshot(visit),
        event_type="carefusion.visit.updated",
        event_payload={"visit_id": visit.id},
    )
    return model_snapshot(visit)


@router.post("/prescriptions", status_code=status.HTTP_201_CREATED)
def create_prescription(
    payload: PrescriptionCreate,
    provider_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    import uuid
    prescription_id = f"RX-{uuid.uuid4().hex[:12].upper()}"
    
    prescription = TelehealthPrescription(
        org_id=user.org_id,
        prescription_id=prescription_id,
        provider_id=provider_id,
        **payload.model_dump(),
    )
    apply_training_mode(prescription, request)
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="telehealth_prescription",
        classification="PHI",
        after_state=model_snapshot(prescription),
        event_type="carefusion.prescription.created",
        event_payload={"prescription_id": prescription.id},
    )
    return model_snapshot(prescription)


@router.get("/prescriptions")
def list_prescriptions(
    request: Request,
    provider_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    visit_id: Optional[str] = None,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, TelehealthPrescription, user.org_id, request.state.training_mode)
    
    if provider_id:
        query = query.filter(TelehealthPrescription.provider_id == provider_id)
    if patient_id:
        query = query.filter(TelehealthPrescription.patient_id == patient_id)
    if visit_id:
        query = query.filter(TelehealthPrescription.visit_id == visit_id)
    
    prescriptions = query.order_by(TelehealthPrescription.created_at.desc()).all()
    return [model_snapshot(rx) for rx in prescriptions]
