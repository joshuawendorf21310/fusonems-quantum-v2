from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.billing_claims import BillingAssistResult, BillingClaim, BillingClaimExportSnapshot
from models.epcr import Patient
from models.qa import QAReview
from models.validation import DataValidationIssue
from models.user import User, UserRole
from utils.tenancy import get_scoped_record, scoped_query
from utils.time import utc_now
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from services.billing.assist_service import BillingAssistEngine


claims_router = APIRouter(
    prefix="/api/billing/claims",
    tags=["Billing Claims"],
    dependencies=[Depends(require_module("BILLING"))],
)

assist_router = APIRouter(
    prefix="/api/billing/assist",
    tags=["Billing Assist"],
    dependencies=[Depends(require_module("BILLING"))],
)


class BillingClaimCreate(BaseModel):
    epcr_patient_id: int
    payer_name: str
    payer_type: str = "private"
    total_charge_cents: int | None = None
    office_ally_batch_id: str | None = None


class BillingClaimResponse(BillingClaimCreate):
    id: int
    status: str
    denial_risk_flags: list[str]
    medical_necessity_snapshot: list[dict[str, Any]]

    class Config:
        from_attributes = True


class ClaimStatusUpdate(BaseModel):
    status: str
    denial_reason: str | None = None
    denial_risk_flags: list[str] | None = None
    office_ally_batch_id: str | None = None


def _get_patient(request: Request, db: Session, user: User, patient_id: int) -> Patient:
    patient = (
        get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
        if patient_id
        else None
    )
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="patient_not_found")
    return patient


def _ensure_assist_result(
    db: Session,
    request: Request,
    user: User,
    patient: Patient,
    force_refresh: bool = False,
) -> BillingAssistResult:
    query = scoped_query(
        db, BillingAssistResult, user.org_id, request.state.training_mode
    ).filter(BillingAssistResult.epcr_patient_id == patient.id)
    existing = query.order_by(BillingAssistResult.created_at.desc()).first()
    if existing and not force_refresh and existing.snapshot_json:
        return existing
    snapshot = BillingAssistEngine.generate(patient)
    payload = {"patient": model_snapshot(patient), "generated_at": snapshot.get("generated_at")}
    before = model_snapshot(existing) if existing else None
    if existing:
        existing.snapshot_json = snapshot
        existing.input_payload = payload
        apply_training_mode(existing, request)
        db.commit()
        db.refresh(existing)
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="update",
            resource="billing_assist_result",
            classification=existing.classification,
            before_state=before,
            after_state=model_snapshot(existing),
            event_type="billing.ai_assist_generated",
            event_payload={"patient_id": patient.id},
        )
        return existing
    new_result = BillingAssistResult(
        org_id=user.org_id,
        epcr_patient_id=patient.id,
        snapshot_json=snapshot,
        input_payload=payload,
    )
    apply_training_mode(new_result, request)
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_assist_result",
        classification=new_result.classification,
        after_state=model_snapshot(new_result),
        event_type="billing.ai_assist_generated",
        event_payload={"patient_id": patient.id},
    )
    return new_result


def _compute_qa_score(review: QAReview | None) -> float:
    if not review or not review.scores:
        return 0.0
    values = [value for value in review.scores.values() if isinstance(value, (int, float))]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _collect_ready_reasons(
    db: Session,
    request: Request,
    user: User,
    patient: Patient,
    assist_result: BillingAssistResult,
) -> tuple[bool, list[dict[str, Any]], dict[str, str], float]:
    reasons: list[dict[str, Any]] = []
    ready = True
    fix_links = {
        "chart": f"/api/epcr/patients/{patient.id}/lock",
        "validation": "/api/validation/issues",
        "qa": "/api/qa/cases",
        "narrative": f"/api/epcr/patients/{patient.id}",
        "assist": f"/api/billing/assist/{patient.id}",
    }

    if not patient.chart_locked:
        ready = False
        reasons.append(
            {
                "code": "chart_unlocked",
                "detail": "Chart must be locked before billing.",
                "severity": "High",
                "fix_link": fix_links["chart"],
            }
        )
    issues = (
        scoped_query(db, DataValidationIssue, user.org_id, request.state.training_mode)
        .filter(
            DataValidationIssue.entity_type == "epcr_patient",
            DataValidationIssue.entity_id == str(patient.id),
            DataValidationIssue.severity == "High",
        )
        .all()
    )
    if issues:
        ready = False
        reasons.append(
            {
                "code": "validation_block",
                "detail": "High severity validation issues exist.",
                "severity": "High",
                "fix_link": fix_links["validation"],
            }
        )
    missing_fields = [
        field
        for field in ("first_name", "last_name", "date_of_birth", "address")
        if not getattr(patient, field)
    ]
    if missing_fields:
        ready = False
        reasons.append(
            {
                "code": "demographics_missing",
                "detail": f"Required demographics are missing: {', '.join(missing_fields)}.",
                "severity": "Medium",
                "fix_link": fix_links["narrative"],
            }
        )
    review = (
        scoped_query(db, QAReview, user.org_id, request.state.training_mode)
        .filter(QAReview.linked_patient_id == patient.id)
        .order_by(QAReview.created_at.desc())
        .first()
    )
    qa_score = _compute_qa_score(review)
    if qa_score < settings.QA_READY_THRESHOLD:
        ready = False
        reasons.append(
            {
                "code": "qa_low_score",
                "detail": f"Latest QA score {qa_score} below threshold {settings.QA_READY_THRESHOLD}.",
                "severity": "Medium",
                "fix_link": fix_links["qa"],
            }
        )
    if not patient.narrative:
        ready = False
        reasons.append(
            {
                "code": "medical_narrative_missing",
                "detail": "Medical necessity narrative is required.",
                "severity": "High",
                "fix_link": fix_links["narrative"],
            }
        )
    return ready, reasons, fix_links, qa_score


def try_auto_create_claim(db: Session, request: Request, user: User, epcr_patient_id: int) -> BillingClaim | None:
    """If AUTO_CLAIM_AFTER_FINALIZE is enabled and ready_check passes, create a draft claim. Returns claim or None."""
    if not getattr(settings, "AUTO_CLAIM_AFTER_FINALIZE", False):
        return None
    try:
        patient = _get_patient(request, db, user, epcr_patient_id)
        assist_result = _ensure_assist_result(db, request, user, patient)
        ready, _, _, _ = _collect_ready_reasons(db, request, user, patient, assist_result)
        if not ready:
            return None
        existing = (
            db.query(BillingClaim)
            .filter(BillingClaim.org_id == user.org_id, BillingClaim.epcr_patient_id == epcr_patient_id)
            .first()
        )
        if existing:
            return existing
        demographics_snapshot = model_snapshot(patient)
        medical_snapshot = assist_result.snapshot_json.get("medical_necessity_hints") or []
        claim = BillingClaim(
            org_id=user.org_id,
            epcr_patient_id=patient.id,
            payer_name="To be assigned",
            payer_type="private",
            total_charge_cents=0,
            office_ally_batch_id="",
            denial_risk_flags=assist_result.snapshot_json.get("denial_risk_flags", []),
            demographics_snapshot=demographics_snapshot,
            medical_necessity_snapshot=medical_snapshot,
        )
        apply_training_mode(claim, request)
        db.add(claim)
        db.commit()
        db.refresh(claim)
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="billing_claim",
            classification=claim.classification,
            after_state=model_snapshot(claim),
            event_type="billing.claim.auto_created",
            event_payload={"claim_id": claim.id, "patient_id": patient.id},
        )
        return claim
    except Exception:
        return None


@claims_router.post("", response_model=BillingClaimResponse, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: BillingClaimCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    patient = _get_patient(request, db, user, payload.epcr_patient_id)
    assist_result = _ensure_assist_result(db, request, user, patient)
    demographics_snapshot = model_snapshot(patient)
    medical_snapshot = assist_result.snapshot_json.get("medical_necessity_hints") or []
    claim = BillingClaim(
        org_id=user.org_id,
        epcr_patient_id=patient.id,
        payer_name=payload.payer_name,
        payer_type=payload.payer_type,
        total_charge_cents=payload.total_charge_cents,
        office_ally_batch_id=payload.office_ally_batch_id or "",
        denial_risk_flags=assist_result.snapshot_json.get("denial_risk_flags", []),
        demographics_snapshot=demographics_snapshot,
        medical_necessity_snapshot=medical_snapshot,
    )
    apply_training_mode(claim, request)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_claim",
        classification=claim.classification,
        after_state=model_snapshot(claim),
        event_type="billing.claim.created",
        event_payload={"claim_id": claim.id, "patient_id": patient.id},
    )
    return model_snapshot(claim)


@claims_router.get("/ready_check")
def ready_check(
    epcr_patient_id: int = Query(..., alias="epcr_patient_id"),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.dispatcher)),
):
    patient = _get_patient(request, db, user, epcr_patient_id)
    assist_result = _ensure_assist_result(db, request, user, patient)
    ready, reasons, fix_links, qa_score = _collect_ready_reasons(
        db, request, user, patient, assist_result
    )
    return {
        "pass": ready,
        "reasons": reasons,
        "fix_links": fix_links,
        "qa_score": qa_score,
        "medical_necessity": assist_result.snapshot_json.get("medical_necessity_hints"),
    }


def _build_export_bundle(
    claim: BillingClaim,
    patient: Patient,
    assist_payload: dict[str, Any],
) -> dict[str, Any]:
    demographics = {
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth,
        "address": patient.address,
        "phone": patient.phone,
    }
    trip = {
        "incident_number": patient.incident_number,
        "locked_at": patient.locked_at.isoformat() if patient.locked_at else None,
        "transport_miles": claim.demographics_snapshot.get("transport_miles")
        or (patient.vitals or {}).get("transport_miles")
        or 0,
    }
    coding = assist_payload.get("coding_suggestions") or {}
    timestamps = {
        "chart_created": patient.created_at.isoformat() if patient.created_at else None,
        "chart_locked": patient.locked_at.isoformat() if patient.locked_at else None,
        "exported_at": claim.exported_at.isoformat() if claim.exported_at else None,
    }
    signature_flags = {
        "narrative_present": bool(patient.narrative),
        "processed_ocr": bool(patient.ocr_snapshots),
    }
    pcs_indicators = {"procedures_present": bool(patient.procedures)}
    return {
        "claim_id": claim.id,
        "batch_id": claim.office_ally_batch_id,
        "demographics": demographics,
        "trip": trip,
        "coding": {
            "icd10": coding,
            "snomed": [],
            "rxnorm": [],
        },
        "medical_necessity": assist_payload.get("medical_necessity_hints", []),
        "mileage": trip["transport_miles"],
        "timestamps": timestamps,
        "signature_flags": signature_flags,
        "pcs_indicators": pcs_indicators,
    }


@claims_router.get("/{claim_id}")
def get_claim(
    claim_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    claim = (
        scoped_query(db, BillingClaim, user.org_id, request.state.training_mode)
        .filter(BillingClaim.id == claim_id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="claim_not_found")
    patient = _get_patient(request, db, user, claim.epcr_patient_id)
    return {
        "id": claim.id,
        "status": claim.status,
        "payer": claim.payer_name,
        "denial_risk_flags": claim.denial_risk_flags,
        "office_ally_batch_id": claim.office_ally_batch_id,
        "demographics": claim.demographics_snapshot,
        "medical_snapshot": claim.medical_necessity_snapshot,
        "patient": {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "incident": patient.incident_number,
        },
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
        "updated_at": claim.updated_at.isoformat() if claim.updated_at else None,
    }


@claims_router.get("/{claim_id}/export/office_ally")
def export_office_ally(
    claim_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    claim = (
        scoped_query(db, BillingClaim, user.org_id, request.state.training_mode)
        .filter(BillingClaim.id == claim_id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="claim_not_found")
    patient = _get_patient(request, db, user, claim.epcr_patient_id)
    assist_result = _ensure_assist_result(db, request, user, patient)
    ready, reasons, _ = _collect_ready_reasons(db, request, user, patient, assist_result)
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "chart_not_ready", "reasons": reasons},
        )
    bundle = _build_export_bundle(claim, patient, assist_result.snapshot_json)
    snapshot = BillingClaimExportSnapshot(
        org_id=user.org_id,
        claim_id=claim.id,
        payload=bundle,
    )
    apply_training_mode(snapshot, request)
    db.add(snapshot)
    claim.status = "exported"
    claim.exported_at = utc_now()
    if not claim.office_ally_batch_id:
        claim.office_ally_batch_id = f"oa-{claim.id}-{int(utc_now().timestamp())}"
    db.commit()
    db.refresh(claim)
    db.refresh(snapshot)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="export",
        resource="billing_claim_export_snapshot",
        classification=snapshot.classification,
        after_state=model_snapshot(snapshot),
        event_type="billing.exported",
        event_payload={"claim_id": claim.id, "export_id": snapshot.id},
    )
    return {"export": bundle}


@claims_router.post("/{claim_id}/status")
def update_claim_status(
    claim_id: int,
    payload: ClaimStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    claim = (
        scoped_query(db, BillingClaim, user.org_id, request.state.training_mode)
        .filter(BillingClaim.id == claim_id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="claim_not_found")
    before = model_snapshot(claim)
    status_map = {"submitted": "submitted", "denied": "denied", "paid": "paid", "void": "void", "ready": "ready"}
    if payload.status not in status_map:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")
    claim.status = payload.status
    claim.office_ally_batch_id = payload.office_ally_batch_id or claim.office_ally_batch_id
    if payload.status == "submitted":
        claim.submitted_at = utc_now()
        event_type = "billing.submitted"
    elif payload.status == "denied":
        if not payload.denial_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="denial_reason_required",
            )
        claim.denial_reason = payload.denial_reason
        claim.denial_risk_flags = payload.denial_risk_flags or claim.denial_risk_flags
        event_type = "billing.denied"
    elif payload.status == "paid":
        claim.paid_at = utc_now()
        event_type = "billing.paid"
    else:
        event_type = f"billing.{payload.status}"
    db.commit()
    db.refresh(claim)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="billing_claim",
        classification=claim.classification,
        before_state=before,
        after_state=model_snapshot(claim),
        event_type=event_type,
        event_payload={"claim_id": claim.id, "status": claim.status},
    )
    return {"status": "ok", "claim_id": claim.id, "new_status": claim.status}


@assist_router.get("/{epcr_patient_id}")
def get_billing_assist(
    epcr_patient_id: int,
    refresh: bool = Query(False),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    patient = _get_patient(request, db, user, epcr_patient_id)
    result = _ensure_assist_result(db, request, user, patient, force_refresh=refresh)
    return {
        "snapshot": result.snapshot_json,
        "generated_at": result.created_at.isoformat() if result.created_at else None,
    }
