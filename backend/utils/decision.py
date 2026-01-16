from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from fastapi import Request
from sqlalchemy.orm import Session

from core.config import settings
from models.user import User
from utils.audit import record_audit
from utils.time import utc_now


DECISION_PRIORITY = {
    "BLOCK": 3,
    "REQUIRE_CONFIRMATION": 2,
    "WARN": 1,
    "ALLOW": 0,
}


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def hash_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _score_confidence(decision: str, reasons: list[dict[str, Any]]) -> float:
    base = 1.0
    penalties = 0.0
    for reason in reasons:
        severity = reason.get("severity", "Low").lower()
        if severity == "high":
            penalties += 0.25
        elif severity == "medium":
            penalties += 0.15
        else:
            penalties += 0.05
    if decision == "REQUIRE_CONFIRMATION":
        penalties += 0.1
    if decision == "BLOCK":
        penalties += 0.2
    return max(0.0, min(1.0, base - penalties))


@dataclass
class DecisionBuilder:
    component: str
    component_version: str
    reasons: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    next_actions: list[dict[str, Any]] = field(default_factory=list)
    decision_override: Optional[str] = None

    def add_reason(
        self,
        rule_id: str,
        message: str,
        severity: str = "Medium",
        decision: str = "WARN",
        evidence_refs: Optional[list[str]] = None,
    ) -> None:
        self.reasons.append(
            {
                "rule_id": rule_id,
                "message": message,
                "severity": severity,
                "decision": decision,
                "evidence_refs": evidence_refs or [],
            }
        )

    def add_evidence(
        self,
        evidence_type: str,
        source: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        payload = {
            "type": evidence_type,
            "source": source,
            "metadata": metadata or {},
        }
        payload["hash"] = hash_payload(payload)
        self.evidence.append(payload)
        return payload["hash"]

    def add_next_action(
        self,
        action_id: str,
        label: str,
        endpoint: str,
        required_role: str,
    ) -> None:
        self.next_actions.append(
            {
                "action_id": action_id,
                "label": label,
                "endpoint": endpoint,
                "required_role": required_role,
            }
        )

    def _resolve_decision(self) -> str:
        if self.decision_override:
            return self.decision_override
        highest = "ALLOW"
        for reason in self.reasons:
            candidate = reason.get("decision", "WARN")
            if DECISION_PRIORITY.get(candidate, 0) > DECISION_PRIORITY.get(highest, 0):
                highest = candidate
        return highest

    def build(
        self,
        input_payload: dict[str, Any],
        request: Optional[Request],
    ) -> dict[str, Any]:
        decision = self._resolve_decision()
        rule_ids = [reason["rule_id"] for reason in self.reasons]
        packet = {
            "decision": decision,
            "rule_ids": rule_ids,
            "reasons": [
                {
                    "rule_id": reason["rule_id"],
                    "message": reason["message"],
                    "severity": reason.get("severity", "Medium"),
                    "evidence_refs": reason.get("evidence_refs", []),
                }
                for reason in self.reasons
            ],
            "evidence": self.evidence,
            "next_allowed_actions": self.next_actions,
            "confidence": _score_confidence(decision, self.reasons),
            "audit_ref": {
                "audit_id": "",
                "timestamp": "",
            },
        }
        packet["evidence"].append(
            {
                "type": "config",
                "source": "SMART_MODE",
                "hash": hash_payload({"smart_mode": settings.SMART_MODE}),
                "metadata": {"smart_mode": settings.SMART_MODE},
            }
        )
        packet["input_hash"] = hash_payload(input_payload)
        return packet


def finalize_decision_packet(
    db: Session,
    request: Optional[Request],
    user: User,
    builder: DecisionBuilder,
    input_payload: dict[str, Any],
    classification: str,
    action: str,
    resource: str,
    reason_code: str,
) -> dict[str, Any]:
    packet = builder.build(input_payload, request)
    decision_id = f"dec_{uuid4().hex}"
    timestamp = utc_now()
    packet["audit_ref"]["audit_id"] = decision_id
    packet["audit_ref"]["timestamp"] = timestamp.isoformat()
    output_hash = hash_payload(packet)
    record_audit(
        db=db,
        request=request,
        user=user,
        action=action,
        resource=resource,
        outcome=packet["decision"].title(),
        classification=classification,
        training_mode=getattr(request.state, "training_mode", False) if request else False,
        reason_code=reason_code,
        decision_id=decision_id,
        reasoning_component=builder.component,
        reasoning_version=builder.component_version,
        method_used="rules",
        input_hash=packet["input_hash"],
        output_hash=output_hash,
        decision_packet=packet,
    )
    packet["output_hash"] = output_hash
    return packet
