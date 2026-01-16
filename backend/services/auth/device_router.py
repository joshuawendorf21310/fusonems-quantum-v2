from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.device_trust import DeviceTrust
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(prefix="/api/auth/devices", tags=["Device Trust"])


class DeviceEnroll(BaseModel):
    device_id: str
    fingerprint: str = ""


@router.get("")
def list_devices(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    records = (
        scoped_query(db, DeviceTrust, user.org_id, request.state.training_mode)
        .order_by(DeviceTrust.created_at.desc())
        .all()
    )
    return [model_snapshot(record) for record in records]


@router.post("", status_code=status.HTTP_201_CREATED)
def enroll_device(
    payload: DeviceEnroll,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    record = DeviceTrust(
        org_id=user.org_id,
        user_id=user.id,
        device_id=payload.device_id,
        fingerprint=payload.fingerprint,
        trusted=False,
    )
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="device_trust",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="auth.device.enrolled",
        event_payload={"device_id": record.device_id},
    )
    return model_snapshot(record)


@router.post("/{device_id}/approve")
def approve_device(
    device_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    record = (
        scoped_query(db, DeviceTrust, user.org_id, request.state.training_mode)
        .filter(DeviceTrust.device_id == device_id)
        .first()
    )
    if not record:
        return {"status": "not_found"}
    record.trusted = True
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="device_trust",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="auth.device.approved",
        event_payload={"device_id": record.device_id},
    )
    return {"status": "ok", "device_id": record.device_id}
