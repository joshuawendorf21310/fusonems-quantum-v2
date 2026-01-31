from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import require_roles
from models.transportlink import TransportTrip, TransportDocumentSnapshot
from models.user import User, UserRole
from utils.tenancy import get_scoped_record
from utils.write_ops import audit_and_event
from .transport_ai_service import extract_document, ai_refine_extraction
import os

router = APIRouter(prefix="/api/transport")

class ExtractRequest(BaseModel):
    file_id: str

class ExtractResponse(BaseModel):
    extracted_fields: dict
    confidence: dict
    evidence: list
    warnings: list
    snapshot_id: str

class ApplyRequest(BaseModel):
    snapshot_id: str
    accepted_fields: dict
    overrides: dict = {}

@router.post("/trips/{trip_id}/documents/{doc_type}/extract", response_model=ExtractResponse)
def extract_doc(trip_id: int, doc_type: str, req: ExtractRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.facility_admin, UserRole.facility_user))):
    from core.config import settings
    trip = get_scoped_record(db, None, TransportTrip, trip_id, user)
    # TODO: fetch file text by file_id (stub: use dummy text)
    text = "DUMMY PDF TEXT for extraction"
    fields, confidence, evidence, warnings = extract_document(doc_type, text)
    # Optionally refine with AI
    if settings.SUPPORT_AI_ENABLED:
        ai_result = ai_refine_extraction(doc_type, fields, text)
        if ai_result:
            fields = ai_result.get('fields', fields)
            confidence = ai_result.get('confidence', confidence)
            evidence = ai_result.get('evidence', evidence)
            warnings = ai_result.get('warnings', warnings)
    snap = TransportDocumentSnapshot(
        org_id=trip.org_id,
        trip_id=trip.id,
        doc_type=doc_type,
        file_id=req.file_id,
        extracted_json=fields,
        confidence_json=confidence,
        evidence_json=evidence,
        warnings_json=warnings,
        provider="ai" if ai_enabled else "deterministic",
        created_by_user_id=user.id,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    audit_and_event(db, user, trip, f"transport.document.extracted", extra={"snapshot_id": str(snap.id)})
    return ExtractResponse(
        extracted_fields=fields,
        confidence=confidence,
        evidence=evidence,
        warnings=warnings,
        snapshot_id=str(snap.id),
    )

class ApplyResponse(BaseModel):
    trip: dict

@router.post("/trips/{trip_id}/documents/{doc_type}/apply", response_model=ApplyResponse)
def apply_doc(trip_id: int, doc_type: str, req: ApplyRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.facility_admin, UserRole.facility_user))):
    trip = get_scoped_record(db, None, TransportTrip, trip_id, user)
    snap = db.query(TransportDocumentSnapshot).filter_by(id=req.snapshot_id, trip_id=trip_id, doc_type=doc_type).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    # Apply accepted_fields and overrides to trip (stub: just update payload)
    trip.payload = {**trip.payload, **req.accepted_fields, **req.overrides}
    db.add(trip)
    db.commit()
    audit_and_event(db, user, trip, f"transport.document.applied", extra={"snapshot_id": str(snap.id), "applied_fields": req.accepted_fields, "overrides": req.overrides})
    return ApplyResponse(trip=trip.__dict__)
