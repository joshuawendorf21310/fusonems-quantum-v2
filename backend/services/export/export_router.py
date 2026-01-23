import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.database import get_db, get_hems_db
from core.guards import require_module
from core.security import require_roles
from models.ai_console import AiInsight
from models.billing import BillingRecord
from models.cad import Call
from models.epcr import Patient
from models.exports import DataExportManifest
from models.hems import HemsMission
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from utils.workflows import upsert_workflow_state

router = APIRouter(
    prefix="/api/export",
    tags=["Exports"],
    dependencies=[Depends(require_module("EXPORTS"))],
)


def _hash_manifest(manifest: dict) -> str:
    raw = json.dumps(manifest, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@router.post("/full", status_code=status.HTTP_201_CREATED)
def export_full(
    request: Request,
    db: Session = Depends(get_db),
    hems_db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    if request.state.training_mode:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TRAINING_MODE_EXPORT_BLOCKED")

    counts = {
        "cad_calls": scoped_query(db, Call, user.org_id, request.state.training_mode).count(),
        "epcr_patients": scoped_query(db, Patient, user.org_id, request.state.training_mode).count(),
        "billing_records": scoped_query(
            db, BillingRecord, user.org_id, request.state.training_mode
        ).count(),
        "ai_insights": scoped_query(db, AiInsight, user.org_id, request.state.training_mode).count(),
        "hems_missions": scoped_query(
            hems_db, HemsMission, user.org_id, request.state.training_mode
        ).count(),
    }
    manifest = {
        "org_id": user.org_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "schema_version": "v2",
        "chain_of_custody": {
            "requested_by": user.email,
            "reason": "Full export",
        },
    }
    export_hash = _hash_manifest(manifest)
    record = DataExportManifest(
        org_id=user.org_id,
        manifest=manifest,
        export_hash=export_hash,
        training_mode=False,
    )
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="export",
        resource="data_export_manifest",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="exports.full.created",
        event_payload={"export_id": record.id},
    )
    upsert_workflow_state(
        db=db,
        org_id=user.org_id,
        workflow_key="data_export_full",
        resource_type="data_export_manifest",
        resource_id=str(record.id),
        status="completed",
        last_step="manifest_generated",
        metadata={"export_hash": export_hash},
        classification=record.classification,
        training_mode=request.state.training_mode,
    )
    csv_preview = "resource,count\n" + "\n".join(
        f"{key},{value}" for key, value in counts.items()
    )
    return {
        "manifest": manifest,
        "export_hash": export_hash,
        "csv_preview": csv_preview,
        "pdf_bundle": "pending_generation",
    }


@router.get("/history")
def export_history(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    return scoped_query(db, DataExportManifest, user.org_id, request.state.training_mode).order_by(
        DataExportManifest.created_at.desc()
    ).all()
