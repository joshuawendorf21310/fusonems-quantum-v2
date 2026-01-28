from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.database import get_telehealth_db
from core.security import require_roles
from models.telehealth import (
    TelehealthProvider,
    TelehealthPatient,
    TelehealthAppointment,
    TelehealthVisit,
    ProviderAvailability,
)
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(prefix="/api/carefusion/patient", tags=["CareFusion Patient"])


class PatientRegistration(BaseModel):
    name: str
    email: str
    phone: str = ""
    date_of_birth: Optional[datetime] = None
    address: str = ""
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    insurance_provider: str = ""
    insurance_policy_number: str = ""
    medical_history: str = ""
    allergies: str = ""
    current_medications: str = ""


class AppointmentBooking(BaseModel):
    provider_id: str
    appointment_type: str = "consultation"
    reason_for_visit: str
    scheduled_start: datetime
    patient_notes: str = ""


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    patient_notes: Optional[str] = None


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_patient(
    payload: PatientRegistration,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    import uuid
    patient_id = f"PT-{uuid.uuid4().hex[:12].upper()}"
    
    patient = TelehealthPatient(
        org_id=user.org_id,
        patient_id=patient_id,
        **payload.model_dump(),
    )
    apply_training_mode(patient, request)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="telehealth_patient",
        classification="PHI",
        after_state=model_snapshot(patient),
        event_type="carefusion.patient.registered",
        event_payload={"patient_id": patient.id},
    )
    return model_snapshot(patient)


@router.get("/profile/{patient_id}")
def get_patient_profile(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    patient = (
        scoped_query(db, TelehealthPatient, user.org_id, request.state.training_mode)
        .filter(TelehealthPatient.patient_id == patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return model_snapshot(patient)


@router.get("/providers")
def list_providers(
    request: Request,
    specialty: Optional[str] = None,
    accepts_new_patients: Optional[bool] = True,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    query = scoped_query(db, TelehealthProvider, user.org_id, request.state.training_mode)
    query = query.filter(TelehealthProvider.status == "active")
    
    if specialty:
        query = query.filter(TelehealthProvider.specialty.ilike(f"%{specialty}%"))
    if accepts_new_patients is not None:
        query = query.filter(TelehealthProvider.accepts_new_patients == accepts_new_patients)
    
    providers = query.order_by(TelehealthProvider.name).all()
    return [model_snapshot(provider) for provider in providers]


@router.get("/providers/{provider_id}")
def get_provider_detail(
    provider_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    provider = (
        scoped_query(db, TelehealthProvider, user.org_id, request.state.training_mode)
        .filter(TelehealthProvider.provider_id == provider_id)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return model_snapshot(provider)


@router.get("/providers/{provider_id}/availability")
def get_provider_availability(
    provider_id: str,
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    query = scoped_query(db, ProviderAvailability, user.org_id, request.state.training_mode)
    query = query.filter(ProviderAvailability.provider_id == provider_id)
    query = query.filter(ProviderAvailability.is_available == True)
    
    if start_date or end_date:
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(
                or_(
                    ProviderAvailability.override_date >= start_dt,
                    ProviderAvailability.override_date.is_(None)
                )
            )
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(
                or_(
                    ProviderAvailability.override_date <= end_dt,
                    ProviderAvailability.override_date.is_(None)
                )
            )
    
    availability = query.order_by(ProviderAvailability.day_of_week, ProviderAvailability.start_time).all()
    return [model_snapshot(slot) for slot in availability]


@router.post("/appointments", status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentBooking,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    provider = (
        scoped_query(db, TelehealthProvider, user.org_id, request.state.training_mode)
        .filter(TelehealthProvider.provider_id == payload.provider_id)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    
    import uuid
    appointment_id = f"APT-{uuid.uuid4().hex[:12].upper()}"
    
    scheduled_end = payload.scheduled_start.replace(
        hour=payload.scheduled_start.hour + 1
    )
    
    appointment = TelehealthAppointment(
        org_id=user.org_id,
        appointment_id=appointment_id,
        scheduled_end=scheduled_end,
        **payload.model_dump(),
    )
    apply_training_mode(appointment, request)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="telehealth_appointment",
        classification="PHI",
        after_state=model_snapshot(appointment),
        event_type="carefusion.appointment.booked",
        event_payload={"appointment_id": appointment.id},
    )
    return model_snapshot(appointment)


@router.get("/appointments")
def list_patient_appointments(
    request: Request,
    patient_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    query = scoped_query(db, TelehealthAppointment, user.org_id, request.state.training_mode)
    
    if patient_id:
        query = query.filter(TelehealthAppointment.patient_id == patient_id)
    if status_filter:
        query = query.filter(TelehealthAppointment.status == status_filter)
    
    appointments = query.order_by(TelehealthAppointment.scheduled_start.desc()).all()
    return [model_snapshot(apt) for apt in appointments]


@router.get("/appointments/{appointment_id}")
def get_appointment_detail(
    appointment_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    appointment = (
        scoped_query(db, TelehealthAppointment, user.org_id, request.state.training_mode)
        .filter(TelehealthAppointment.appointment_id == appointment_id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return model_snapshot(appointment)


@router.put("/appointments/{appointment_id}")
def update_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    appointment = (
        scoped_query(db, TelehealthAppointment, user.org_id, request.state.training_mode)
        .filter(TelehealthAppointment.appointment_id == appointment_id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    
    before_state = model_snapshot(appointment)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)
    
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


@router.delete("/appointments/{appointment_id}")
def cancel_appointment(
    appointment_id: str,
    cancellation_reason: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    appointment = (
        scoped_query(db, TelehealthAppointment, user.org_id, request.state.training_mode)
        .filter(TelehealthAppointment.appointment_id == appointment_id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    
    before_state = model_snapshot(appointment)
    appointment.status = "cancelled"
    appointment.cancellation_reason = cancellation_reason
    
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
        event_type="carefusion.appointment.cancelled",
        event_payload={"appointment_id": appointment.id},
    )
    return {"status": "cancelled", "appointment_id": appointment_id}


@router.get("/visits")
def list_patient_visits(
    request: Request,
    patient_id: Optional[str] = None,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    query = scoped_query(db, TelehealthVisit, user.org_id, request.state.training_mode)
    
    if patient_id:
        query = query.filter(TelehealthVisit.patient_id == patient_id)
    
    visits = query.order_by(TelehealthVisit.created_at.desc()).all()
    return [model_snapshot(visit) for visit in visits]


@router.get("/visits/{visit_id}")
def get_visit_detail(
    visit_id: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    visit = (
        scoped_query(db, TelehealthVisit, user.org_id, request.state.training_mode)
        .filter(TelehealthVisit.visit_id == visit_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return model_snapshot(visit)
