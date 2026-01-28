from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from models.compliance import ForensicAuditLog
from models.user import User


def record_audit(
    db: Session,
    request: Request,
    user: User,
    action: str,
    resource: str,
    outcome: str,
    classification: str = "OPS",
    training_mode: bool = False,
    reason_code: str = "",
    before_state: Optional[dict[str, Any]] = None,
    after_state: Optional[dict[str, Any]] = None,
    decision_id: str = "",
    reasoning_component: str = "",
    reasoning_version: str = "",
    method_used: str = "",
    input_hash: str = "",
    output_hash: str = "",
    decision_packet: Optional[dict[str, Any]] = None,
) -> None:
    audit = ForensicAuditLog(
        org_id=str(user.org_id),
        classification=classification,
        training_mode=training_mode,
        actor_email=user.email,
        actor_role=user.role,
        action=action,
        resource=resource,
        reason_code=reason_code,
        decision_id=decision_id,
        reasoning_component=reasoning_component,
        reasoning_version=reasoning_version,
        method_used=method_used,
        input_hash=input_hash,
        output_hash=output_hash,
        decision_packet=decision_packet,
        device_fingerprint=request.headers.get("x-device-fingerprint", ""),
        ip_address=request.client.host if request.client else "",
        session_id=request.headers.get("x-session-id", ""),
        before_state=before_state,
        after_state=after_state,
        outcome=outcome,
    )
    db.add(audit)
    db.commit()
