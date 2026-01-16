from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.inspection import inspect as sa_inspect

from fastapi import Request
from sqlalchemy.orm import Session

from models.user import User
from utils.audit import record_audit
from utils.classification import normalize_classification
from utils.events import event_bus
from utils.time import utc_now


def _json_safe(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def model_snapshot(model_obj: Any) -> dict:
    if model_obj is None:
        return {}
    try:
        mapper = sa_inspect(model_obj)
        if hasattr(mapper, "attrs"):
            data = {attr.key: getattr(model_obj, attr.key) for attr in mapper.attrs}
            return _json_safe(data)
    except Exception:
        pass
    data = dict(getattr(model_obj, "__dict__", {}) or {})
    data.pop("_sa_instance_state", None)
    return _json_safe(data)


def apply_training_mode(model_obj: Any, request: Optional[Request]) -> None:
    if request is None:
        return
    if hasattr(model_obj, "training_mode"):
        training_flag = getattr(request.state, "training_mode", False)
        setattr(model_obj, "training_mode", training_flag)
        if training_flag and hasattr(model_obj, "classification"):
            setattr(model_obj, "classification", "TRAINING_ONLY")


def audit_and_event(
    db: Session,
    request: Optional[Request],
    user: User,
    action: str,
    resource: str,
    classification: str,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    event_type: Optional[str] = None,
    event_payload: Optional[dict] = None,
    reason_code: str = "WRITE",
    decision_packet: Optional[dict] = None,
    reasoning_component: str = "",
    reasoning_version: str = "",
    method_used: str = "",
    input_hash: str = "",
    output_hash: str = "",
    decision_id: str = "",
    schema_name: str = "public",
) -> None:
    training_mode = False
    classification = normalize_classification(classification)
    if request is not None:
        record_audit(
            db=db,
            request=request,
            user=user,
            action=action,
            resource=resource,
            outcome="Allowed",
            classification=classification,
            training_mode=getattr(request.state, "training_mode", False),
            reason_code=reason_code,
            before_state=before_state,
            after_state=after_state,
            decision_packet=decision_packet,
            reasoning_component=reasoning_component,
            reasoning_version=reasoning_version,
            method_used=method_used,
            input_hash=input_hash,
            output_hash=output_hash,
            decision_id=decision_id,
        )
        device_id = request.headers.get("x-device-id", "")
        server_time = getattr(request.state, "server_time", utc_now())
        drift_seconds = getattr(request.state, "drift_seconds", 0)
        drifted = getattr(request.state, "drifted", False)
        training_mode = getattr(request.state, "training_mode", False)
    else:
        device_id = ""
        server_time = utc_now()
        drift_seconds = 0
        drifted = False
    if event_type:
        payload = event_payload or {}
        payload.setdefault("classification", classification)
        payload.setdefault("resource", resource)
        event_bus.publish(
            db=db,
            org_id=user.org_id,
            event_type=event_type,
            payload=payload,
            actor_id=user.id,
            actor_role=user.role,
            device_id=device_id,
            server_time=server_time,
            drift_seconds=drift_seconds,
            drifted=drifted,
            training_mode=training_mode,
            schema_name=schema_name,
        )
