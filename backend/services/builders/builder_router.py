from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.builders import BuilderChangeLog, BuilderRegistry
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/builders",
    tags=["Builder Registry"],
    dependencies=[Depends(require_module("BUILDERS"))],
)


class BuilderCreate(BaseModel):
    builder_key: str
    version: str = "v1"
    status: str = "active"
    description: str = ""
    impacted_modules: list[str] = []


class BuilderResponse(BuilderCreate):
    id: int
    last_changed_by: Optional[int] = None
    last_changed_at: Optional[str] = None

    class Config:
        from_attributes = True


class BuilderPatch(BaseModel):
    version: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    impacted_modules: Optional[list[str]] = None
    change_summary: str = ""  # for audit log


class BuilderChangeResponse(BaseModel):
    id: int
    builder_key: str
    change_summary: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/registry", response_model=list[BuilderResponse])
def list_builders(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    builders = (
        scoped_query(db, BuilderRegistry, user.org_id, request.state.training_mode)
        .order_by(BuilderRegistry.builder_key.asc())
        .all()
    )
    return [model_snapshot(builder) for builder in builders]


@router.post("/registry", response_model=BuilderResponse, status_code=status.HTTP_201_CREATED)
def create_builder(
    payload: BuilderCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    registry = BuilderRegistry(
        **payload.model_dump(),
        org_id=user.org_id,
        last_changed_by=user.id,
    )
    apply_training_mode(registry, request)
    db.add(registry)
    db.commit()
    db.refresh(registry)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="builder_registry",
        classification="NON_PHI",
        after_state=model_snapshot(registry),
        event_type="builders.registry.created",
        event_payload={"builder_key": registry.builder_key},
    )
    return model_snapshot(registry)


@router.patch("/registry/{builder_key}")
def update_builder(
    builder_key: str,
    payload: BuilderPatch,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    registry = (
        scoped_query(db, BuilderRegistry, user.org_id, request.state.training_mode)
        .filter(BuilderRegistry.builder_key == builder_key)
        .first()
    )
    if not registry:
        return {"status": "not_found"}
    before = model_snapshot(registry)
    data = payload.model_dump(exclude_unset=True)
    data.pop("change_summary", None)
    for key, value in data.items():
        if value is not None:
            setattr(registry, key, value)
    registry.last_changed_by = user.id
    db.commit()

    change = BuilderChangeLog(
        org_id=user.org_id,
        builder_key=registry.builder_key,
        change_summary=payload.change_summary or "Update",
        before_state=before,
        after_state=model_snapshot(registry),
        created_by=user.id,
    )
    apply_training_mode(change, request)
    db.add(change)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="builder_registry",
        classification="NON_PHI",
        before_state=before,
        after_state=model_snapshot(registry),
        event_type="builders.registry.updated",
        event_payload={"builder_key": registry.builder_key},
    )
    return {"status": "ok", "builder_key": registry.builder_key}


@router.get("/logs", response_model=list[BuilderChangeResponse])
def list_builder_logs(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    logs = scoped_query(db, BuilderChangeLog, user.org_id, request.state.training_mode).order_by(
        BuilderChangeLog.created_at.desc()
    )
    return [
        BuilderChangeResponse(
            id=log.id,
            builder_key=log.builder_key,
            change_summary=log.change_summary,
            created_at=log.created_at.isoformat() if log.created_at else None,
        )
        for log in logs
    ]
