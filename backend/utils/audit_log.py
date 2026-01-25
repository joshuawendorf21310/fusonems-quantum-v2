from typing import Any

from sqlalchemy.orm import Session

from models.audit_event import AuditEvent


def record_audit_event(
    db: Session,
    *,
    org_id: str,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        org_id=org_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta_data=metadata or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
