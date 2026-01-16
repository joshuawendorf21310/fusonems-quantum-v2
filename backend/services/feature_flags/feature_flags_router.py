from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.feature_flags import FeatureFlag
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/feature-flags",
    tags=["Feature Flags"],
    dependencies=[Depends(require_module("FEATURE_FLAGS"))],
)


class FlagCreate(BaseModel):
    flag_key: str
    module_key: str
    enabled: bool = False
    scope: str = "org"
    rules: dict = {}


class FlagResponse(FlagCreate):
    id: int

    class Config:
        from_attributes = True


class FlagPatch(BaseModel):
    enabled: Optional[bool] = None
    rules: Optional[dict] = None
    scope: Optional[str] = None


@router.get("", response_model=list[FlagResponse])
def list_flags(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    return scoped_query(db, FeatureFlag, user.org_id, request.state.training_mode).order_by(
        FeatureFlag.flag_key.asc()
    )


@router.post("", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
def create_flag(
    payload: FlagCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    flag = FeatureFlag(org_id=user.org_id, **payload.dict())
    apply_training_mode(flag, request)
    db.add(flag)
    db.commit()
    db.refresh(flag)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="feature_flag",
        classification="NON_PHI",
        after_state=model_snapshot(flag),
        event_type="feature_flags.created",
        event_payload={"flag_key": flag.flag_key},
    )
    return flag


@router.patch("/{flag_key}")
def update_flag(
    flag_key: str,
    payload: FlagPatch,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    flag = (
        scoped_query(db, FeatureFlag, user.org_id, request.state.training_mode)
        .filter(FeatureFlag.flag_key == flag_key)
        .first()
    )
    if not flag:
        return {"status": "not_found"}
    before = model_snapshot(flag)
    if payload.enabled is not None:
        flag.enabled = payload.enabled
    if payload.rules is not None:
        flag.rules = payload.rules
    if payload.scope is not None:
        flag.scope = payload.scope
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="feature_flag",
        classification="NON_PHI",
        before_state=before,
        after_state=model_snapshot(flag),
        event_type="feature_flags.updated",
        event_payload={"flag_key": flag.flag_key},
    )
    return {"status": "ok", "flag_key": flag.flag_key}
