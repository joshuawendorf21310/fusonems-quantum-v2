from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles, require_on_shift, require_trusted_device
from models.epcr import Patient
from models.user import User, UserRole
from utils.legal import enforce_legal_hold
from utils.decision import DecisionBuilder, finalize_decision_packet, hash_payload
from utils.events import event_bus
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from utils.tenancy import get_scoped_record, scoped_query

OCR_DEVICE_TYPES = {
    "monitor": ["heart_rate", "pulse_rate", "spo2", "bp_systolic", "bp_diastolic", "etco2", "temperature"],
    "ventilator": ["vent_mode", "fio2", "peep", "tidal_volume", "resp_rate", "pressure_support"],
    "pump": ["medication_name", "dose_rate", "dose_units", "volume_remaining", "concentration"],
}
OCR_MIN_CONFIDENCE = 0.85
NEMSIS_RULES = {
    "WI": {
        "required": ["first_name", "last_name", "date_of_birth", "incident_number"],
        "vitals": ["hr", "bp_systolic", "bp_diastolic", "spo2"],
        "ventilator_fields": ["vent_mode", "fio2", "peep"],
    }
}

router = APIRouter(
    prefix="/api/epcr",
    tags=["ePCR"],
    dependencies=[Depends(require_module("EPCR"))],
)


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    incident_number: str
    vitals: dict = {}
    interventions: list = []
    medications: list = []
    procedures: list = []
    labs: list = []
    cct_interventions: list = []
    ocr_snapshots: list = []
    narrative: str = ""
    nemsis_version: str = "3.5.1"
    nemsis_state: str = "WI"


class PatientResponse(PatientCreate):
    id: int

    class Config:
        from_attributes = True


@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    enforce_legal_hold(db, user.org_id, "epcr_patient", payload.incident_number, "create")
    patient = Patient(**payload.dict(), org_id=user.org_id)
    apply_training_mode(patient, request)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="epcr_patient",
        classification=patient.classification,
        after_state=model_snapshot(patient),
        event_type="epcr.patient.created",
        event_payload={"patient_id": patient.id, "incident_number": patient.incident_number},
    )
    return patient


class OCRField(BaseModel):
    field: str
    value: str | float | int | None = None
    confidence: float = 0.0
    bbox: dict | None = None
    page: int | None = None
    source: str | None = None


class OCRIngest(BaseModel):
    device_type: str
    device_name: str = ""
    fields: list[OCRField] | dict = {}
    confidence: float = 0.0
    captured_at: str = ""
    raw_text: str = ""


class NarrativeUpdate(BaseModel):
    narrative: str


class LabEntry(BaseModel):
    lab_type: str
    values: dict
    collected_at: str = ""


class CCTIntervention(BaseModel):
    intervention: str
    details: dict = {}
    performed_at: str = ""


def _map_ocr_fields(patient: Patient, fields: list[dict]) -> None:
    mapping = {
        "heart_rate": ("vitals", "hr"),
        "pulse_rate": ("vitals", "pulse"),
        "spo2": ("vitals", "spo2"),
        "bp_systolic": ("vitals", "bp_systolic"),
        "bp_diastolic": ("vitals", "bp_diastolic"),
        "etco2": ("vitals", "etco2"),
        "temperature": ("vitals", "temp"),
    }
    for entry in fields:
        key = entry.get("field")
        value = entry.get("value")
        mapped = mapping.get(key)
        if mapped:
            bucket, field = mapped
            current = getattr(patient, bucket) or {}
            current[field] = value
            setattr(patient, bucket, current)
        if key == "medication_name" and value:
            entry_payload = {"name": value, "source": entry.get("source") or "ocr"}
            patient.medications = list(patient.medications or []) + [entry_payload]
        if key == "procedure" and value:
            patient.procedures = list(patient.procedures or []) + [value]

    if any(entry.get("source") == "ventilator" for entry in fields):
        details = {entry.get("field"): entry.get("value") for entry in fields if entry.get("field") in OCR_DEVICE_TYPES["ventilator"]}
        if details:
            patient.cct_interventions = list(patient.cct_interventions or []) + [
                {"intervention": "Ventilator", "details": details}
            ]
    pump_fields = {entry.get("field"): entry.get("value") for entry in fields if entry.get("source") == "pump"}
    if pump_fields.get("medication_name"):
        med_detail = {
            "name": pump_fields.get("medication_name"),
            "dose_rate": pump_fields.get("dose_rate"),
            "dose_units": pump_fields.get("dose_units"),
            "concentration": pump_fields.get("concentration"),
            "volume_remaining": pump_fields.get("volume_remaining"),
            "source": "pump",
        }
        patient.medications = list(patient.medications or []) + [med_detail]


@router.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="epcr_patient",
        classification=patient.classification,
        after_state=model_snapshot(patient),
        event_type="RECORD_ACCESSED",
        event_payload={"patient_id": patient.id, "resource": "epcr"},
        reason_code="READ",
    )
    return patient


@router.post("/patients/{patient_id}/ocr", status_code=status.HTTP_201_CREATED)
def ingest_ocr(
    patient_id: int,
    payload: OCRIngest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    builder = DecisionBuilder(component="ocr_validator", component_version="v1")
    if payload.device_type not in OCR_DEVICE_TYPES:
        builder.add_reason(
            "OCR.DEVICE.UNSUPPORTED.v1",
            "Device type is not supported for OCR ingestion.",
            severity="High",
            decision="BLOCK",
        )
        decision = finalize_decision_packet(
            db=db,
            request=request,
            user=user,
            builder=builder,
            input_payload=payload.dict(),
            classification="PHI",
            action="ocr_ingest",
            resource="epcr_patient",
            reason_code="SMART_POLICY",
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=decision)
    raw_fields = payload.fields
    if isinstance(raw_fields, dict):
        structured_fields = [
            {
                "field": key,
                "value": value,
                "confidence": payload.confidence or 0.0,
                "bbox": None,
                "page": None,
                "source": payload.device_type,
            }
            for key, value in raw_fields.items()
        ]
    else:
        structured_fields = [
            {
                "field": entry_dict.get("field"),
                "value": entry_dict.get("value"),
                "confidence": entry_dict.get("confidence", payload.confidence or 0.0),
                "bbox": entry_dict.get("bbox"),
                "page": entry_dict.get("page"),
                "source": entry_dict.get("source") or payload.device_type,
            }
            for entry_dict in [
                entry.dict() if hasattr(entry, "dict") else entry for entry in raw_fields
            ]
        ]
    for entry in structured_fields:
        entry["hash"] = hash_payload(entry)
        entry["evidence_hash"] = builder.add_evidence(
            "ocr_field",
            f"ocr:{payload.device_type}",
            {
                "field": entry.get("field"),
                "value": entry.get("value"),
                "confidence": entry.get("confidence"),
            },
        )
    unknown_fields = [
        entry["field"]
        for entry in structured_fields
        if entry.get("field") not in OCR_DEVICE_TYPES[payload.device_type]
    ]
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    enforce_legal_hold(db, user.org_id, "epcr_patient", str(patient.id), "update")
    before = model_snapshot(patient)
    snapshot = payload.dict()
    snapshot["fields"] = structured_fields
    snapshot["unknown_fields"] = unknown_fields
    low_conf_fields = [field for field in structured_fields if field.get("confidence", 0) < OCR_MIN_CONFIDENCE]
    snapshot["requires_review"] = bool(low_conf_fields)
    snapshots = list(patient.ocr_snapshots or [])
    snapshots.append(snapshot)
    patient.ocr_snapshots = snapshots
    _map_ocr_fields(patient, structured_fields)
    conflict_refs = []
    for field in structured_fields:
        field_name = field.get("field")
        field_value = str(field.get("value") or "").strip()
        if field_name == "first_name" and field_value and field_value != patient.first_name:
            conflict_refs.append(field.get("evidence_hash"))
        if field_name == "last_name" and field_value and field_value != patient.last_name:
            conflict_refs.append(field.get("evidence_hash"))
        if field_name == "date_of_birth" and field_value and field_value != patient.date_of_birth:
            conflict_refs.append(field.get("evidence_hash"))
        if field_name == "dnr" and field_value.lower() in {"true", "yes", "dnr", "do not resuscitate"}:
            conflict_refs.append(field.get("evidence_hash"))
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="epcr_patient",
        classification=patient.classification,
        before_state=before,
        after_state=model_snapshot(patient),
        event_type="epcr.patient.ocr_ingested",
        event_payload={"patient_id": patient.id, "source": "ocr"},
    )
    for field in low_conf_fields:
        builder.add_reason(
            "OCR.CONFIDENCE.REQUIRE_CONFIRM.v1",
            f"Low confidence for field {field.get('field')}.",
            severity="Medium",
            decision="REQUIRE_CONFIRMATION",
            evidence_refs=[field.get("evidence_hash")],
        )
    if conflict_refs:
        builder.add_reason(
            "OCR.CONFLICT.DEMOGRAPHICS.v1",
            "OCR values conflict with patient demographics.",
            severity="High",
            decision="REQUIRE_CONFIRMATION",
            evidence_refs=conflict_refs,
        )
    if unknown_fields:
        builder.add_reason(
            "OCR.FIELD.UNKNOWN.WARN.v1",
            "OCR contained fields that are not mapped for this device type.",
            severity="Low",
            decision="WARN",
            evidence_refs=[
                field.get("evidence_hash")
                for field in structured_fields
                if field.get("field") in unknown_fields
            ],
        )
    if not builder.reasons:
        builder.add_reason(
            "OCR.INGEST.ALLOW.v1",
            "OCR ingestion succeeded with no policy conflicts.",
            severity="Low",
            decision="ALLOW",
        )
    decision = finalize_decision_packet(
        db=db,
        request=request,
        user=user,
        builder=builder,
        input_payload={"patient_id": patient.id, "device_type": payload.device_type, "fields": structured_fields},
        classification=patient.classification,
        action="ocr_ingest",
        resource="epcr_patient",
        reason_code="SMART_POLICY",
    )
    event_bus.publish(
        db=db,
        org_id=user.org_id,
        event_type="ocr.ingested",
        payload={
            "patient_id": patient.id,
            "device_type": payload.device_type,
            "field_hashes": [field.get("evidence_hash") for field in structured_fields],
            "decision": decision.get("decision"),
        },
        actor_id=user.id,
        actor_role=user.role,
        device_id=request.headers.get("x-device-id", ""),
        server_time=getattr(request.state, "server_time", None),
        drift_seconds=getattr(request.state, "drift_seconds", 0),
        drifted=getattr(request.state, "drifted", False),
        training_mode=getattr(request.state, "training_mode", False),
    )
    return {
        "status": "ingested",
        "patient_id": patient.id,
        "snapshots": len(snapshots),
        "unknown_fields": unknown_fields,
        "requires_review": snapshot["requires_review"],
        "decision": decision,
    }


@router.get("/ocr/profiles")
def list_ocr_profiles():
    return {"device_types": OCR_DEVICE_TYPES, "min_confidence": OCR_MIN_CONFIDENCE}


@router.post("/patients/{patient_id}/narrative")
def update_narrative(
    patient_id: int,
    payload: NarrativeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    enforce_legal_hold(db, user.org_id, "epcr_patient", str(patient.id), "update")
    before = model_snapshot(patient)
    patient.narrative = payload.narrative
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="epcr_patient",
        classification=patient.classification,
        before_state=before,
        after_state=model_snapshot(patient),
        event_type="epcr.patient.narrative.updated",
        event_payload={"patient_id": patient.id, "field": "narrative"},
    )
    return {"status": "ok", "patient_id": patient.id}


@router.post("/patients/{patient_id}/labs", status_code=status.HTTP_201_CREATED)
def add_lab(
    patient_id: int,
    payload: LabEntry,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    enforce_legal_hold(db, user.org_id, "epcr_patient", str(patient.id), "update")
    before = model_snapshot(patient)
    labs = list(patient.labs or [])
    labs.append(payload.dict())
    patient.labs = labs
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="epcr_patient",
        classification=patient.classification,
        before_state=before,
        after_state=model_snapshot(patient),
        event_type="epcr.patient.labs.added",
        event_payload={"patient_id": patient.id, "lab_type": payload.lab_type},
    )
    return {"status": "ok", "patient_id": patient.id}


@router.post("/patients/{patient_id}/cct", status_code=status.HTTP_201_CREATED)
def add_cct_intervention(
    patient_id: int,
    payload: CCTIntervention,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    enforce_legal_hold(db, user.org_id, "epcr_patient", str(patient.id), "update")
    before = model_snapshot(patient)
    entries = list(patient.cct_interventions or [])
    entries.append(payload.dict())
    patient.cct_interventions = entries
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="epcr_patient",
        classification=patient.classification,
        before_state=before,
        after_state=model_snapshot(patient),
        event_type="epcr.patient.cct.added",
        event_payload={"patient_id": patient.id, "intervention": payload.intervention},
    )
    return {"status": "ok", "patient_id": patient.id}


@router.get("/patients/{patient_id}/nemsis/validate")
def validate_nemsis(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    ruleset = NEMSIS_RULES.get(getattr(patient, "nemsis_state", "WI"), NEMSIS_RULES["WI"])
    required = [(field, getattr(patient, field, None)) for field in ruleset["required"]]
    required.extend(
        [
            (f"vitals.{key}", patient.vitals.get(key) if patient.vitals else None)
            for key in ruleset["vitals"]
        ]
    )
    if patient.chart_locked and not patient.narrative:
        required.append(("narrative", None))
    if patient.cct_interventions and not patient.labs:
        required.append(("labs", None))
    if patient.cct_interventions:
        vent_checks = [
            entry
            for entry in patient.cct_interventions
            if entry.get("intervention") == "Ventilator"
        ]
        if vent_checks:
            vent_details = vent_checks[-1].get("details", {})
            for key in ruleset["ventilator_fields"]:
                if not vent_details.get(key):
                    required.append((f"ventilator.{key}", None))
    missing = [field for field, value in required if not value]
    ocr_review = [
        snapshot for snapshot in (patient.ocr_snapshots or []) if snapshot.get("requires_review")
    ]
    status_label = "PASS" if not missing else "FAIL"
    return {
        "status": status_label,
        "missing": missing,
        "version": patient.nemsis_version,
        "ocr_review_required": len(ocr_review),
    }


@router.get("/patients/{patient_id}/exports/nemsis")
def export_nemsis(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    payload = {
        "nemsis_version": patient.nemsis_version,
        "incident_number": patient.incident_number,
        "patient": {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth,
        },
        "vitals": patient.vitals,
        "procedures": patient.procedures,
        "medications": patient.medications,
        "labs": patient.labs,
        "cct_interventions": patient.cct_interventions,
        "narrative": patient.narrative,
    }
    return {"status": "ok", "export": payload}


@router.get("/patients", response_model=list[PatientResponse])
def list_patients(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, Patient, user.org_id, request.state.training_mode).order_by(
        Patient.created_at.desc()
    ).all()


@router.post("/patients/{patient_id}/lock")
def lock_chart(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    enforce_legal_hold(db, user.org_id, "epcr_patient", str(patient.id), "update")
    before = model_snapshot(patient)
    patient.chart_locked = True
    patient.locked_at = datetime.utcnow()
    patient.locked_by = user.email
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="epcr_patient",
        classification=patient.classification,
        before_state=before,
        after_state=model_snapshot(patient),
        event_type="CHART_LOCKED",
        event_payload={"patient_id": patient.id, "locked_by": user.email},
    )
    return {"status": "locked", "patient_id": patient.id}
