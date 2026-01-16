from core.config import settings
from core.database import SessionLocal
from models.compliance import ForensicAuditLog
from models.communications import CommsTranscript


def _register(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Smart Mode User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_smart_mode_disabled_ocr_decision(client):
    original = settings.SMART_MODE
    settings.SMART_MODE = False
    try:
        headers = _register(client, "smart-ocr@example.com", "SmartOCR")
        patient = client.post(
            "/api/epcr/patients",
            headers=headers,
            json={
                "first_name": "Riley",
                "last_name": "Morgan",
                "date_of_birth": "1990-01-01",
                "incident_number": "INC-1001",
            },
        ).json()
        response = client.post(
            f"/api/epcr/patients/{patient['id']}/ocr",
            headers=headers,
            json={
                "device_type": "monitor",
                "fields": [{"field": "heart_rate", "value": "120", "confidence": 0.4}],
                "confidence": 0.4,
            },
        )
    finally:
        settings.SMART_MODE = original
    assert response.status_code == 201
    payload = response.json()
    assert payload["decision"]["decision"] == "REQUIRE_CONFIRMATION"
    assert "OCR.CONFIDENCE.REQUIRE_CONFIRM.v1" in payload["decision"]["rule_ids"]

    session = SessionLocal()
    audit = (
        session.query(ForensicAuditLog)
        .filter(ForensicAuditLog.reasoning_component == "ocr_validator")
        .first()
    )
    session.close()
    assert audit is not None
    assert audit.input_hash
    assert audit.output_hash


def test_billing_readiness_decision(client):
    original = settings.SMART_MODE
    settings.SMART_MODE = False
    try:
        headers = _register(client, "smart-billing@example.com", "SmartBilling")
        response = client.post(
            "/api/billing/invoices",
            headers=headers,
            json={
                "patient_name": "Taylor",
                "invoice_number": "INV-9001",
                "payer": "Medicare",
                "amount_due": 1200,
            },
        )
        assert response.status_code == 201
        response = client.post(
            "/api/billing/readiness",
            headers=headers,
            json={"invoice_number": "INV-9001"},
        )
    finally:
        settings.SMART_MODE = original
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"]["decision"] == "BLOCK"
    assert "BILL.CMS.CLAIM_PAYLOAD.MINIMUM.v1" in payload["decision"]["rule_ids"]

    session = SessionLocal()
    audit = (
        session.query(ForensicAuditLog)
        .filter(ForensicAuditLog.reasoning_component == "billing_readiness")
        .first()
    )
    session.close()
    assert audit is not None
    assert audit.input_hash
    assert audit.output_hash


def test_comms_transcript_storage(client):
    original = settings.SMART_MODE
    settings.SMART_MODE = False
    try:
        headers = _register(client, "smart-comms@example.com", "SmartComms")
        call = client.post(
            "/api/comms/calls",
            headers=headers,
            json={
                "caller": "+15551231234",
                "recipient": "+15551239999",
                "direction": "inbound",
                "duration_seconds": 0,
                "recording_url": "",
                "disposition": "new",
            },
        ).json()
        response = client.post(
            f"/api/comms/calls/{call['id']}/transcript",
            headers=headers,
            json={
                "transcript_text": "Caller reports chest pain.",
                "segments": [{"start_time": 0.0, "end_time": 2.1, "speaker": "caller", "text": "Chest pain", "confidence": 0.82}],
                "confidence": 0.82,
                "method_used": "local",
            },
        )
    finally:
        settings.SMART_MODE = original
    assert response.status_code == 201
    payload = response.json()
    assert payload["decision"]["decision"] in {"ALLOW", "REQUIRE_CONFIRMATION"}

    session = SessionLocal()
    transcript = (
        session.query(CommsTranscript)
        .filter(CommsTranscript.call_id == call["id"])
        .first()
    )
    session.close()
    assert transcript is not None
