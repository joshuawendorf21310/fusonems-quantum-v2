from __future__ import annotations

from typing import Any


AUDIENCE_TEMPLATES = {
    "emt": "Field Guidance",
    "paramedic": "Field Guidance",
    "supervisor": "Supervisor Review",
    "billing": "Billing Review",
    "legal": "Legal/Audit Summary",
    "audit": "Legal/Audit Summary",
    "default": "Operational Guidance",
}


def render_explanation(decision_packet: dict[str, Any], audience: str = "default") -> dict[str, Any]:
    label = AUDIENCE_TEMPLATES.get(audience, AUDIENCE_TEMPLATES["default"])
    decision = decision_packet.get("decision", "ALLOW")
    reasons = decision_packet.get("reasons", [])
    lines = []
    for reason in reasons:
        rule_id = reason.get("rule_id", "")
        message = reason.get("message", "")
        if rule_id and message:
            lines.append(f"{rule_id}: {message}")
        elif message:
            lines.append(message)
    summary = "No issues detected."
    if decision == "BLOCK":
        summary = "Action blocked due to policy enforcement."
    elif decision == "REQUIRE_CONFIRMATION":
        summary = "Action requires confirmation based on policy thresholds."
    elif decision == "WARN":
        summary = "Action allowed with warnings."
    return {
        "label": label,
        "decision": decision,
        "summary": summary,
        "details": lines,
        "confidence": decision_packet.get("confidence", 1.0),
        "audit_ref": decision_packet.get("audit_ref", {}),
    }
