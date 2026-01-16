from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.ai_registry import AiOutputRegistry
from models.user import User, UserRole
from utils.ai_registry import register_ai_output
from utils.tenancy import get_scoped_record, scoped_query
from utils.write_ops import audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/ai-registry",
    tags=["AI Registry"],
    dependencies=[Depends(require_module("AI_CONSOLE"))],
)


class AiOutputCreate(BaseModel):
    model_name: str
    model_version: str
    prompt: str
    output_text: str
    advisory_level: str = "ADVISORY"
    classification: str = "OPS"
    input_refs: list[dict] = []
    config_snapshot: dict = {}


class AiOutputReview(BaseModel):
    acceptance_state: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_output(
    payload: AiOutputCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    record = register_ai_output(
        db=db,
        org_id=user.org_id,
        model_name=payload.model_name,
        model_version=payload.model_version,
        prompt=payload.prompt,
        output_text=payload.output_text,
        advisory_level=payload.advisory_level,
        classification=payload.classification,
        input_refs=payload.input_refs,
        config_snapshot=payload.config_snapshot,
        training_mode=request.state.training_mode,
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="ai_output",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="ai_registry.output.created",
        event_payload={"ai_output_id": record.id},
    )
    return model_snapshot(record)


@router.get("")
def list_outputs(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(
        db, AiOutputRegistry, user.org_id, request.state.training_mode
    ).order_by(AiOutputRegistry.created_at.desc()).all()


@router.post("/{output_id}/review")
def review_output(
    output_id: int,
    payload: AiOutputReview,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director)),
):
    record = get_scoped_record(
        db,
        request,
        AiOutputRegistry,
        output_id,
        user,
        resource_label="ai_output",
    )
    before = model_snapshot(record)
    record.acceptance_state = payload.acceptance_state
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="review",
        resource="ai_output",
        classification=record.classification,
        before_state=before,
        after_state=model_snapshot(record),
        event_type="ai_registry.output.reviewed",
        event_payload={"ai_output_id": record.id},
    )
    return {"status": "updated", "output_id": record.id}


@router.get("/{output_id}/replay")
def replay_output(
    output_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    record = get_scoped_record(
        db,
        request,
        AiOutputRegistry,
        output_id,
        user,
        resource_label="ai_output",
    )
    return {
        "output_id": record.id,
        "model_name": record.model_name,
        "model_version": record.model_version,
        "prompt_hash": record.prompt_hash,
        "config_snapshot": record.config_snapshot,
        "input_refs": record.input_refs,
        "advisory_level": record.advisory_level,
        "classification": record.classification,
        "output_text": record.output_text,
    }
