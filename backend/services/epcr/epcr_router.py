from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_on_shift, require_roles, require_trusted_device
from models.epcr import Patient
from models.epcr_core import (
    EpcrAssessment,
    EpcrIntervention,
    EpcrMedication,
    EpcrNarrative,
    EpcrRecord,
    EpcrRecordStatus,
    EpcrTimeline,
    EpcrVitals,
    NEMSISValidationResult,
    NEMSISValidationStatus,
    PatientStatus,
)
from models.terminology_builder import TerminologyEntry
from models.user import User, UserRole
from utils.tenancy import scoped_query

from .ai_suggestions import AISuggestions
from .billing_sync import BillingSyncService
from .cad_sync import CADSyncService
from .hospital_notifications import HospitalNotificationService
from .nemsis_export import NEMSISExporter
from .offline_sync import OfflineSyncManager
from .ocr_service import OCRService
from .rule_engine import RuleEngine
from .schematron_service import run_schematron
from .voice_service import VoiceService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/epcr",
    tags=["ePCR"],
    dependencies=[Depends(require_module("EPCR"))],
)


class RecordCreate(BaseModel):
    patient_id: int
    incident_number: str
    record_number: Optional[str] = None
    chief_complaint: Optional[str] = ""
    dispatch_datetime: Optional[datetime] = None
    scene_arrival_datetime: Optional[datetime] = None
    hospital_arrival_datetime: Optional[datetime] = None
    patient_destination: Optional[str] = ""
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    nemsis_state: str = "WI"
    training_mode: bool = False


class QuickPCRCreate(BaseModel):
    """Create patient + record in one call (e.g. from tablet or new PCR form)."""
    incident_number: str
    unit: Optional[str] = ""
    response_date: Optional[str] = None
    response_time: Optional[str] = None
    patient_first_name: str = ""
    patient_last_name: str = ""
    patient_dob: str = ""
    patient_gender: str = ""
    patient_age: Optional[str] = ""
    chief_complaint: str = ""
    chief_complaint_code: Optional[str] = ""
    complaint_onset: Optional[str] = ""
    bp_systolic: Optional[str] = ""
    bp_diastolic: Optional[str] = ""
    heart_rate: Optional[str] = ""
    respiratory_rate: Optional[str] = ""
    oxygen_saturation: Optional[str] = ""
    temperature: Optional[str] = ""
    glucose: Optional[str] = ""
    level_of_consciousness: Optional[str] = ""
    assessment_findings: Optional[str] = ""
    interventions: Optional[str] = ""
    medications: Optional[str] = ""
    narrative: str = ""
    disposition: Optional[str] = ""
    destination_facility: Optional[str] = ""
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class RecordUpdate(BaseModel):
    chief_complaint: Optional[str] = None
    chief_complaint_code: Optional[str] = None  # ICD-10 from terminology builder
    patient_destination: Optional[str] = None
    scene_departure_datetime: Optional[datetime] = None
    hospital_arrival_datetime: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    status: Optional[EpcrRecordStatus] = None


class RecordResponse(BaseModel):
    id: int
    patient_id: int
    incident_number: str
    record_number: str
    status: EpcrRecordStatus
    chief_complaint: str
    chief_complaint_code: Optional[str] = ""  # ICD-10 from terminology (NEMSIS-constrained)
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class VitalEntry(BaseModel):
    values: Dict[str, Any]
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "manual"
    notes: str = ""
    provider_id: Optional[int] = None


class AssessmentEntry(BaseModel):
    assessment_summary: str
    clinical_impression: Optional[str] = ""
    impression_code: Optional[str] = ""  # ICD-10 for impression (NEMSIS-constrained)
    plan: Optional[str] = ""
    chief_complaint: Optional[str] = ""


class InterventionEntry(BaseModel):
    procedure_name: str
    description: Optional[str] = ""
    performed_at: Optional[datetime] = None
    location: Optional[str] = "scene"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MedicationEntry(BaseModel):
    medication_name: str
    ndc: Optional[str] = ""
    dose: Optional[str] = ""
    units: Optional[str] = ""
    route: Optional[str] = ""
    administration_time: Optional[datetime] = None
    condition_icd10: Optional[str] = ""  # ICD-10 for medication history (e.g. condition for which med is taken)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NarrativeEntry(BaseModel):
    narrative_text: Optional[str] = ""
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    voice_transcription: Optional[str] = None
    origin: str = "manual"


class OCRSnapshotEntry(BaseModel):
    device_type: str
    device_name: str = ""
    fields: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    captured_at: Optional[datetime] = None
    raw_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    event_type: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any]


class ValidationStatusResponse(BaseModel):
    status: str
    validator_version: str
    errors: List[Dict[str, Any]]
    missing_fields: List[str]
    validation_timestamp: datetime

    class Config:
        orm_mode = True


def _get_record(db: Session, user: User, record_id: int) -> EpcrRecord:
    record = scoped_query(db, EpcrRecord, user.org_id).filter(EpcrRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ePCR record not found")
    return record


# ---------------------------------------------------------------------------
# NEMSIS-constrained terminology for ePCR (ICD-10 chief complaint, etc.)
# ---------------------------------------------------------------------------

class ICD10Option(BaseModel):
    code: str
    description: str
    alternate_text: Optional[str] = None
    nemsis_element_ref: Optional[str] = None


class TerminologySuggestRequest(BaseModel):
    query: str
    code_set: str = "icd10"


@router.post("/terminology/suggest")
def epcr_terminology_suggest(
    payload: TerminologySuggestRequest,
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.dispatcher)),
):
    """AI-suggest ICD-10, SNOMED, or RXNorm codes for ePCR (chief complaint, interventions, meds). Same logic as founder terminology suggest."""
    from services.founder.terminology_router import do_suggest_terminology
    return do_suggest_terminology(payload.query, payload.code_set)


@router.get("/terminology/icd10", response_model=List[ICD10Option])
def list_icd10_for_epcr(
    use_case: Optional[str] = None,  # diagnosis (chief complaint), impression, medication_history; omit = all
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.dispatcher)),
):
    """
    List ICD-10 codes from the founder terminology builder (NEMSIS-constrained).
    Use in ePCR for:
    - Chief complaint / diagnosis (use_case=diagnosis)
    - Impressions / clinical impression (use_case=impression)
    - Medication history / condition for which med is taken (use_case=medication_history)
    Omit use_case to return all ICD-10 entries for the org.
    """
    q = (
        scoped_query(db, TerminologyEntry, user.org_id, None)
        .filter(TerminologyEntry.code_set == "icd10", TerminologyEntry.active == True)
    )
    if use_case:
        q = q.filter(TerminologyEntry.use_case == use_case)
    rows = q.order_by(TerminologyEntry.sort_order, TerminologyEntry.code).all()
    return [
        ICD10Option(
            code=r.code,
            description=r.description,
            alternate_text=r.alternate_text,
            nemsis_element_ref=r.nemsis_element_ref,
        )
        for r in rows
    ]


def _append_timeline(db: Session, record: EpcrRecord, event_type: str, description: str, metadata: Dict[str, Any] | None = None):
    entry = EpcrTimeline(
        org_id=record.org_id,
        record_id=record.id,
        event_type=event_type,
        description=description,
        timestamp=datetime.now(timezone.utc),
        metadata=metadata or {},
    )
    db.add(entry)
    db.commit()


@router.post("/records", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: RecordCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    patient = scoped_query(db, Patient, user.org_id).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    record = EpcrRecord(
        org_id=user.org_id,
        patient_id=payload.patient_id,
        record_number=payload.record_number or f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        incident_number=payload.incident_number,
        chief_complaint=payload.chief_complaint,
        chief_complaint_code=payload.chief_complaint_code or "",
        dispatch_datetime=payload.dispatch_datetime,
        scene_arrival_datetime=payload.scene_arrival_datetime,
        hospital_arrival_datetime=payload.hospital_arrival_datetime,
        patient_destination=payload.patient_destination,
        custom_fields=payload.custom_fields,
        nemsis_state=payload.nemsis_state,
        training_mode=payload.training_mode,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    _append_timeline(db, record, "record.created", "Record created", {"created_by": user.id, "incident_number": record.incident_number})
    return record


class QuickPCRResponse(BaseModel):
    id: int
    patient_id: int
    record_id: int
    incident_number: str

    class Config:
        orm_mode = True


@router.post("/pcrs", response_model=QuickPCRResponse, status_code=status.HTTP_201_CREATED)
def create_quick_pcr(
    payload: QuickPCRCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    """Create patient + ePCR record in one call (tablet / new PCR form)."""
    from utils.write_ops import apply_training_mode
    incident_number = (payload.incident_number or "").strip() or f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    first_name = (payload.patient_first_name or "").strip() or "Unknown"
    last_name = (payload.patient_last_name or "").strip() or "Unknown"
    dob = (payload.patient_dob or "").strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    patient = Patient(
        org_id=user.org_id,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        incident_number=incident_number,
        chief_complaint=payload.chief_complaint or "",
        gender=(payload.patient_gender or "").strip(),
        vitals={
            "bp_systolic": payload.bp_systolic,
            "bp_diastolic": payload.bp_diastolic,
            "heart_rate": payload.heart_rate,
            "respiratory_rate": payload.respiratory_rate,
            "oxygen_saturation": payload.oxygen_saturation,
            "temperature": payload.temperature,
            "glucose": payload.glucose,
        },
        narrative=payload.narrative or "",
        status=PatientStatus.DRAFT,
    )
    apply_training_mode(patient, request)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    record = EpcrRecord(
        org_id=user.org_id,
        patient_id=patient.id,
        record_number=f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        incident_number=incident_number,
        chief_complaint=payload.chief_complaint or "",
        chief_complaint_code=(payload.chief_complaint_code or "").strip() or "",
        patient_destination=payload.destination_facility or "",
        custom_fields={
            "unit": payload.unit,
            "response_date": payload.response_date,
            "response_time": payload.response_time,
            "complaint_onset": payload.complaint_onset,
            "level_of_consciousness": payload.level_of_consciousness,
            "assessment_findings": payload.assessment_findings,
            "interventions": payload.interventions,
            "medications": payload.medications,
            "disposition": payload.disposition,
            **payload.custom_fields,
        },
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    _append_timeline(db, record, "record.created", "Quick PCR created", {"created_by": user.id, "incident_number": incident_number})
    return QuickPCRResponse(id=record.id, patient_id=patient.id, record_id=record.id, incident_number=incident_number)


class PCRListItem(BaseModel):
    id: int
    incident_number: str
    patient_name: str
    chief_complaint: str
    status: str
    created_at: datetime
    unit: Optional[str] = None
    priority: Optional[str] = None
    disposition: Optional[str] = None

    class Config:
        orm_mode = True


@router.get("/pcrs/recent", response_model=List[PCRListItem])
def list_pcrs_recent(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    """Recent PCRs for dashboard (id, incident_number, patient_name, chief_complaint, status, created_at)."""
    records = (
        scoped_query(db, EpcrRecord, user.org_id)
        .order_by(EpcrRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for r in records:
        patient = db.query(Patient).filter(Patient.id == r.patient_id, Patient.org_id == user.org_id).first()
        name = f"{patient.first_name} {patient.last_name}".strip() if patient else "Unknown"
        cf = r.custom_fields or {}
        out.append(
            PCRListItem(
                id=r.id,
                incident_number=r.incident_number,
                patient_name=name,
                chief_complaint=r.chief_complaint or "",
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
                created_at=r.created_at,
                unit=cf.get("unit"),
                priority=None,
                disposition=cf.get("disposition"),
            )
        )
    return out


class StatisticsResponse(BaseModel):
    total_pcrs: int
    pending: int
    in_progress: int
    completed: int
    today: int


@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    """Aggregate counts for dashboard."""
    base = scoped_query(db, EpcrRecord, user.org_id)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    total = base.count()
    pending = base.filter(EpcrRecord.status == EpcrRecordStatus.DRAFT).count()
    in_progress = base.filter(EpcrRecord.status == EpcrRecordStatus.ACTIVE).count()
    completed = base.filter(EpcrRecord.status.in_([EpcrRecordStatus.FINALIZED, EpcrRecordStatus.SUBMITTED])).count()
    today = base.filter(EpcrRecord.created_at >= today_start).count()
    return StatisticsResponse(total_pcrs=total, pending=pending, in_progress=in_progress, completed=completed, today=today)


class PCRListResponse(BaseModel):
    pcrs: List[PCRListItem]
    total_pages: int


@router.get("/pcrs", response_model=PCRListResponse)
def list_pcrs(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    """List PCRs with pagination for list page."""
    query = scoped_query(db, EpcrRecord, user.org_id)
    if status and status != "all":
        try:
            status_enum = EpcrRecordStatus(status)
            query = query.filter(EpcrRecord.status == status_enum)
        except ValueError:
            pass
    if search:
        query = query.filter(
            EpcrRecord.incident_number.ilike(f"%{search}%") | EpcrRecord.chief_complaint.ilike(f"%{search}%")
        )
    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    records = query.order_by(EpcrRecord.created_at.desc()).offset(offset).limit(limit).all()
    pcrs = []
    for r in records:
        patient = db.query(Patient).filter(Patient.id == r.patient_id, Patient.org_id == user.org_id).first()
        name = f"{patient.first_name} {patient.last_name}".strip() if patient else "Unknown"
        cf = r.custom_fields or {}
        pcrs.append(
            PCRListItem(
                id=r.id,
                incident_number=r.incident_number,
                patient_name=name,
                chief_complaint=r.chief_complaint or "",
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
                created_at=r.created_at,
                unit=cf.get("unit"),
                priority=None,
                disposition=cf.get("disposition"),
            )
        )
    return PCRListResponse(pcrs=pcrs, total_pages=total_pages)


@router.get("/records", response_model=List[RecordResponse])
def list_records(
    status_filter: Optional[EpcrRecordStatus] = None,
    patient_id: Optional[int] = None,
    limit: int = 25,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, EpcrRecord, user.org_id)
    if status_filter:
        query = query.filter(EpcrRecord.status == status_filter)
    if patient_id:
        query = query.filter(EpcrRecord.patient_id == patient_id)
    records = query.order_by(EpcrRecord.created_at.desc()).offset(offset).limit(limit).all()
    return records


@router.get("/records/{record_id}", response_model=RecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    return record


@router.patch("/records/{record_id}", response_model=RecordResponse)
def update_record(
    record_id: int,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    updates = payload.dict(exclude_unset=True)
    for attr, value in updates.items():
        if hasattr(record, attr):
            setattr(record, attr, value)
    db.commit()
    db.refresh(record)
    _append_timeline(db, record, "record.updated", "Record updated", {"updates": updates, "updated_by": user.id})
    return record


@router.post("/records/{record_id}/vitals", status_code=status.HTTP_201_CREATED)
def add_vitals(
    record_id: int,
    payload: VitalEntry,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    vitals = EpcrVitals(
        org_id=user.org_id,
        record_id=record.id,
        values=payload.values,
        recorded_at=payload.recorded_at,
        source=payload.source,
        provider_id=payload.provider_id,
        notes=payload.notes,
    )
    db.add(vitals)
    db.commit()
    rule_payload = RuleEngine.validate_record(db, record)
    _append_timeline(db, record, "vitals.recorded", "Vitals recorded", {"values": payload.values, "rule_status": rule_payload["status"]})
    return {"status": rule_payload["status"], "errors": rule_payload.get("errors", [])}


@router.post("/records/{record_id}/assessment", status_code=status.HTTP_201_CREATED)
def add_assessment(
    record_id: int,
    payload: AssessmentEntry,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    assessment = EpcrAssessment(
        org_id=user.org_id,
        record_id=record.id,
        assessment_summary=payload.assessment_summary,
        clinical_impression=payload.clinical_impression,
        impression_code=payload.impression_code or "",
        plan=payload.plan,
        chief_complaint=payload.chief_complaint or record.chief_complaint,
    )
    db.add(assessment)
    db.commit()
    _append_timeline(db, record, "assessment.logged", "Assessment captured", payload.dict())
    return {"id": assessment.id}


@router.post("/records/{record_id}/intervention", status_code=status.HTTP_201_CREATED)
def add_intervention(
    record_id: int,
    payload: InterventionEntry,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    intervention = EpcrIntervention(
        org_id=user.org_id,
        record_id=record.id,
        procedure_name=payload.procedure_name,
        description=payload.description,
        performed_at=payload.performed_at,
        location=payload.location,
        metadata=payload.metadata,
    )
    db.add(intervention)
    db.commit()
    _append_timeline(db, record, "intervention.logged", payload.procedure_name, payload.metadata)
    BillingSyncService.map_to_billing(record, intervention)
    return {"id": intervention.id}


@router.post("/records/{record_id}/medication", status_code=status.HTTP_201_CREATED)
def add_medication(
    record_id: int,
    payload: MedicationEntry,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    medication = EpcrMedication(
        org_id=user.org_id,
        record_id=record.id,
        medication_name=payload.medication_name,
        ndc=payload.ndc or "",
        dose=payload.dose or "",
        units=payload.units or "",
        route=payload.route or "",
        administration_time=payload.administration_time,
        med_metadata={**(payload.metadata or {}), "condition_icd10": payload.condition_icd10 or ""},
    )
    db.add(medication)
    db.commit()
    BillingSyncService.map_to_billing(record, medication)
    _append_timeline(db, record, "medication.administered", payload.medication_name, payload.metadata)
    return {"id": medication.id}


@router.post("/records/{record_id}/narrative", status_code=status.HTTP_201_CREATED)
def add_narrative(
    record_id: int,
    payload: NarrativeEntry,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    patient = scoped_query(db, Patient, user.org_id).filter(Patient.id == record.patient_id).first()
    raw_transcription = payload.voice_transcription or payload.narrative_text or ""
    refined_text = raw_transcription
    if payload.voice_transcription:
        refined_text = VoiceService.refine_transcription(raw_transcription, patient)
        refined_text = VoiceService.generate_narrative_from_voice(refined_text, patient, payload.structured_data)

    narrative = EpcrNarrative(
        org_id=user.org_id,
        record_id=record.id,
        narrative_text=payload.narrative_text or refined_text,
        ai_refined_text=refined_text,
        generation_source=payload.origin,
        metadata={"structured_data": payload.structured_data},
    )
    db.add(narrative)
    db.commit()
    AISuggestions.log_suggestion(record, narrative)
    _append_timeline(db, record, "narrative.generated", "Narrative recorded", {"source": payload.origin})
    return {"id": narrative.id}


@router.post("/records/{record_id}/ocr", status_code=status.HTTP_201_CREATED)
def add_ocr_snapshot(
    record_id: int,
    payload: OCRSnapshotEntry,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    snapshot = OCRService.ingest_snapshot(db, record, payload.model_dump())
    _append_timeline(db, record, "ocr.ingested", "OCR snapshot stored", {"device": payload.device_type})
    return {"id": snapshot.id, "confidence": snapshot.confidence}


@router.post("/records/{record_id}/post", status_code=status.HTTP_200_OK)
def finalize_record(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    record = _get_record(db, user, record_id)
    validation = RuleEngine.validate_record(db, record)
    # NEMSIS 3.5.1 Schematron validation
    schematron = run_schematron(db, record, nemsis_version=record.nemsis_version or "3.5.1")
    all_errors = list(validation.get("errors", []))
    for e in schematron.get("errors", []):
        all_errors.append({"schematron": True, "rule": e.get("rule"), "message": e.get("message"), "fix": e.get("fix")})
    if not schematron.get("passed", True):
        status_value = "fail"
    else:
        status_value = validation.get("status", "fail")
    try:
        status_enum = NEMSISValidationStatus(status_value)
    except ValueError:
        status_enum = NEMSISValidationStatus.FAIL
    validation_entry = NEMSISValidationResult(
        org_id=user.org_id,
        epcr_patient_id=record.patient_id,
        status=status_enum,
        missing_fields=validation.get("missing_fields", []),
        validation_errors=all_errors,
        validator_version="rule-engine-1.0+schematron-3.5.1",
    )
    record.status = EpcrRecordStatus.FINALIZED
    record.finalized_at = datetime.now(timezone.utc)
    record.finalized_by = user.id
    db.add(validation_entry)
    db.commit()
    # Service orchestration - ensure all services work together
    try:
        from services.integration.orchestrator import ServiceOrchestrator
        ServiceOrchestrator.on_epcr_finalized(db, record, user.id)
    except Exception as e:
        logger.error(f"Orchestrator error during ePCR finalization: {e}", exc_info=True)
        # Continue even if orchestrator fails - don't block finalization
    
    # Legacy service calls (kept for backward compatibility)
    AISuggestions.suggest_protocol(record)
    NEMSISExporter.export_record_to_nemsis(record, db=db)
    OfflineSyncManager.queue_record(db, record)
    HospitalNotificationService.queue_notification(db, record)
    CADSyncService.sync_incident(db, record)
    if getattr(settings, "AUTO_CLAIM_AFTER_FINALIZE", False):
        try:
            from services.billing.claims_router import try_auto_create_claim
            try_auto_create_claim(db, request, user, record.patient_id)
        except Exception:
            pass
    response_validation = {**validation, "schematron": schematron, "errors": all_errors}
    _append_timeline(db, record, "record.finalized", "Record posted", {"validation": response_validation})
    return {"record_id": record.id, "validation": response_validation}


@router.get("/records/{record_id}/timeline", response_model=List[TimelineEvent])
def get_timeline(
    record_id: int,
    limit: int = 1000,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    # Limit timeline events to prevent performance issues with records that have many events
    events = db.query(EpcrTimeline).filter(EpcrTimeline.record_id == record.id).order_by(EpcrTimeline.timestamp.asc()).limit(limit).all()
    return events


@router.get("/records/{record_id}/validation", response_model=ValidationStatusResponse)
def get_validation_status(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = _get_record(db, user, record_id)
    validation = (
        db.query(NEMSISValidationResult)
        .filter(NEMSISValidationResult.epcr_patient_id == record.patient_id)
        .order_by(NEMSISValidationResult.validation_timestamp.desc())
        .first()
    )
    if not validation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No validation results yet")
    return validation


@router.get("/records/{record_id}/exports/nemsis")
def export_record_nemsis_xml(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    """Export ePCR record as NEMSIS 3.x XML for state submission. Uses full element map from record + patient + vitals + assessment."""
    record = _get_record(db, user, record_id)
    payload = NEMSISExporter.export_record_to_nemsis(record, db=db)
    elements = payload.get("elements") or {}
    state = payload.get("state") or "WI"
    nemsis_version = payload.get("nemsis_version") or "3.5.1"
    xml_str = NEMSISExporter.elements_to_xml(elements, state=state, nemsis_version=nemsis_version)
    return Response(content=xml_str, media_type="application/xml")


class SubmitToStateRequest(BaseModel):
    state_code: str = Field(..., description="State code (e.g. WI, IL)")


@router.post("/records/{record_id}/submit-to-state")
def submit_record_to_state(
    record_id: int,
    payload: SubmitToStateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Build NEMSIS XML from record and POST to configured state endpoint. Configure WISCONSIN_NEMSIS_ENDPOINT or NEMSIS_STATE_ENDPOINTS (JSON)."""
    record = _get_record(db, user, record_id)
    nemsis_payload = NEMSISExporter.export_record_to_nemsis(record, db=db)
    elements = nemsis_payload.get("elements") or {}
    state = (payload.state_code or record.nemsis_state or "WI").upper()
    nemsis_version = nemsis_payload.get("nemsis_version") or "3.5.1"
    xml_content = NEMSISExporter.elements_to_xml(elements, state=state, nemsis_version=nemsis_version)

    endpoint = None
    if state == "WI" and getattr(settings, "WISCONSIN_NEMSIS_ENDPOINT", None):
        endpoint = settings.WISCONSIN_NEMSIS_ENDPOINT
    if not endpoint and getattr(settings, "NEMSIS_STATE_ENDPOINTS", None):
        try:
            endpoints = json.loads(settings.NEMSIS_STATE_ENDPOINTS or "{}")
            endpoint = endpoints.get(state) or endpoints.get(state.upper())
        except (json.JSONDecodeError, TypeError):
            pass
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No state endpoint configured for {state}. Set WISCONSIN_NEMSIS_ENDPOINT (for WI) or NEMSIS_STATE_ENDPOINTS JSON.",
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                endpoint,
                content=xml_content,
                headers={"Content-Type": "application/xml"},
            )
            return {
                "status": "SUBMITTED" if response.is_success else "FAILED",
                "record_id": record.id,
                "state_code": state,
                "state_response_status": response.status_code,
                "state_response_preview": response.text[:300] if response.text else None,
                "endpoint_used": endpoint,
            }
    except Exception as e:
        logger.exception("State submission failed for record_id=%s", record_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"State submission failed: {e}",
        )
