from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.consent import ConsentProvenance
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/consent",
    tags=["Consent"],
    dependencies=[Depends(require_module("COMPLIANCE"))],
)


class ConsentCreate(BaseModel):
    subject_type: str
    subject_id: str
    policy_hash: str = ""
    context: str = ""
    metadata: dict = {}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_consent(
    payload: ConsentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.medical_director)),
):
    consent = ConsentProvenance(
        org_id=user.org_id,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        policy_hash=payload.policy_hash,
        context=payload.context,
        metadata_json=payload.metadata,
        captured_by=user.email,
        device_id=request.headers.get("x-device-id", "") if request else "",
    )
    apply_training_mode(consent, request)
    db.add(consent)
    db.commit()
    db.refresh(consent)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="consent_provenance",
        classification=consent.classification,
        after_state=model_snapshot(consent),
        event_type="consent.created",
        event_payload={"consent_id": consent.id},
    )
    return consent


@router.get("")
def list_consent(
    request: Request,
    subject_type: str | None = None,
    subject_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    query = scoped_query(db, ConsentProvenance, user.org_id, request.state.training_mode)
    if subject_type:
        query = query.filter(ConsentProvenance.subject_type == subject_type)
    if subject_id:
        query = query.filter(ConsentProvenance.subject_id == subject_id)
    return query.order_by(ConsentProvenance.server_time.desc()).all()
