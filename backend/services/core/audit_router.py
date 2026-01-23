from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from core.auth import require_role
from core.database import get_db
from models.audit_event import AuditEvent
from models.user import UserRole
from pydantic import BaseModel
from utils.audit_log import record_audit_event


router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogPayload(BaseModel):
    action: str
    entity_type: str
    entity_id: str
    before: dict | None = None
    after: dict | None = None
    metadata: dict | None = None
    timestamp: str | None = None


@router.get("")
def list_audit_events(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.founder, UserRole.compliance, UserRole.admin)),
) -> list[dict]:
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.org_id == current_user.org_id)
        .order_by(AuditEvent.timestamp.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": str(event.id),
            "orgId": str(event.org_id),
            "userId": str(event.user_id),
            "action": event.action,
            "entityType": event.entity_type,
            "entityId": event.entity_id,
            "metadata": event.metadata,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        }
        for event in events
    ]


@router.post("/log", status_code=status.HTTP_201_CREATED)
def log_audit_event(
    payload: AuditLogPayload,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.founder, UserRole.compliance, UserRole.admin)),
) -> dict:
    metadata = payload.metadata or {}
    if payload.before is not None:
        metadata["before"] = payload.before
    if payload.after is not None:
        metadata["after"] = payload.after
    if payload.timestamp is not None:
        metadata["timestamp"] = payload.timestamp
    event = record_audit_event(
        db=db,
        org_id=str(current_user.org_id),
        user_id=str(current_user.id),
        action=payload.action,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        metadata=metadata,
    )
    return {
        "id": str(event.id),
        "orgId": str(event.org_id),
        "userId": str(event.user_id),
        "action": event.action,
        "entityType": event.entity_type,
        "entityId": event.entity_id,
        "metadata": event.metadata,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
    }
