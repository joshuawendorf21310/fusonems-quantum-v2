from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.auth import require_role
from core.database import get_db
from models.audit_event import AuditEvent
from models.user import UserRole


router = APIRouter(prefix="/audit", tags=["Audit"])

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
