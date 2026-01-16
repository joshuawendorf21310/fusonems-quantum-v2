from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.user import User, UserRole
from models.workflow import WorkflowState
from utils.tenancy import get_scoped_record, scoped_query
from utils.workflows import upsert_workflow_state
from utils.write_ops import audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/workflows",
    tags=["Workflows"],
    dependencies=[Depends(require_module("AUTOMATION"))],
)


class WorkflowCreate(BaseModel):
    workflow_key: str
    resource_type: str
    resource_id: str
    status: str = "started"
    last_step: str = ""
    interruption_reason: str = ""
    metadata: dict = {}


class WorkflowStatusUpdate(BaseModel):
    status: str
    last_step: str = ""
    interruption_reason: str = ""
    metadata: dict = {}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_workflow(
    payload: WorkflowCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor)),
):
    record = upsert_workflow_state(
        db=db,
        org_id=user.org_id,
        workflow_key=payload.workflow_key,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        status=payload.status,
        last_step=payload.last_step,
        interruption_reason=payload.interruption_reason,
        metadata=payload.metadata,
        classification="OPS",
        training_mode=request.state.training_mode,
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="workflow_state",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="workflows.created",
        event_payload={"workflow_id": record.id},
    )
    return model_snapshot(record)


@router.get("")
def list_workflows(
    request: Request,
    workflow_key: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    query = scoped_query(db, WorkflowState, user.org_id, request.state.training_mode)
    if workflow_key:
        query = query.filter(WorkflowState.workflow_key == workflow_key)
    if resource_type:
        query = query.filter(WorkflowState.resource_type == resource_type)
    if resource_id:
        query = query.filter(WorkflowState.resource_id == resource_id)
    return query.order_by(WorkflowState.created_at.desc()).all()


@router.post("/{workflow_id}/status")
def update_workflow(
    workflow_id: int,
    payload: WorkflowStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor)),
):
    record = get_scoped_record(
        db,
        request,
        WorkflowState,
        workflow_id,
        user,
        resource_label="workflow_state",
    )
    before = model_snapshot(record)
    record.status = payload.status
    record.last_step = payload.last_step
    record.interruption_reason = payload.interruption_reason
    record.metadata_json = payload.metadata or record.metadata_json
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="workflow_state",
        classification=record.classification,
        before_state=before,
        after_state=model_snapshot(record),
        event_type="workflows.updated",
        event_payload={"workflow_id": record.id},
    )
    return {"status": "ok", "workflow_id": record.id}


@router.post("/{workflow_id}/resume")
def resume_workflow(
    workflow_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor)),
):
    record = get_scoped_record(
        db,
        request,
        WorkflowState,
        workflow_id,
        user,
        resource_label="workflow_state",
    )
    before = model_snapshot(record)
    record.status = "resumed"
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="resume",
        resource="workflow_state",
        classification=record.classification,
        before_state=before,
        after_state=model_snapshot(record),
        event_type="workflows.resumed",
        event_payload={"workflow_id": record.id},
    )
    return {"status": "ok", "workflow_id": record.id}
