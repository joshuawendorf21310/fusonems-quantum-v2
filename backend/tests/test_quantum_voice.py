from core.config import settings
from core.database import SessionLocal
from models.compliance import ForensicAuditLog
from models.communications import CommsCallEvent, CommsRecording


def _register(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Voice User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    token = response.json()["access_token"]
    org_id = response.json().get("user", {}).get("org_id")
    return {"Authorization": f"Bearer {token}"}, org_id


def test_telnyx_webhook_idempotent_by_event_id(client):
    headers, org_id = _register(client, "voice@example.com", "VoiceOrg")
    payload = {
        "data": {
            "id": "evt-duplicate",
            "event_type": "call.initiated",
            "occurred_at": "2024-01-01T01:00:00Z",
            "payload": {
                "call_control_id": "call-dup",
                "from": "+15551231234",
                "to": "+15551239999",
                "duration": 0,
                "direction": "inbound",
                "metadata": {"org_id": org_id},
            },
        }
    }
    response = client.post("/api/comms/webhooks/telnyx/test", json=payload)
    assert response.status_code == 200
    response = client.post("/api/comms/webhooks/telnyx/test", json=payload)
    assert response.status_code == 200

    session = SessionLocal()
    events = (
        session.query(CommsCallEvent)
        .filter(CommsCallEvent.provider_event_id == "evt-duplicate")
        .all()
    )
    session.close()
    assert len(events) == 1


def test_recording_download_blocked_by_legal_hold(client):
    headers, org_id = _register(client, "recording@example.com", "RecordingOrg")
    payload = {
        "data": {
            "id": "evt-recording",
            "event_type": "call.recording.saved",
            "occurred_at": "2024-01-01T01:05:00Z",
            "payload": {
                "call_control_id": "call-rec",
                "from": "+15551231234",
                "to": "+15551239999",
                "recording_url": "https://example.com/recording.mp3",
                "metadata": {"org_id": org_id},
            },
        }
    }
    response = client.post("/api/comms/webhooks/telnyx/test", json=payload)
    assert response.status_code == 200

    session = SessionLocal()
    recording = (
        session.query(CommsRecording)
        .filter(CommsRecording.recording_url == "https://example.com/recording.mp3")
        .first()
    )
    session.close()
    assert recording is not None

    hold_payload = {
        "scope_type": "comms_recording",
        "scope_id": str(recording.id),
        "reason": "legal",
    }
    response = client.post("/api/legal-hold", json=hold_payload, headers=headers)
    assert response.status_code == 201

    response = client.get(f"/api/comms/recordings/{recording.id}/download", headers=headers)
    assert response.status_code == 423

    session = SessionLocal()
    audit = (
        session.query(ForensicAuditLog)
        .filter(ForensicAuditLog.resource == "comms_recording", ForensicAuditLog.action == "blocked")
        .first()
    )
    session.close()
    assert audit is not None


def test_telnyx_signature_required(client):
    original = settings.TELNYX_REQUIRE_SIGNATURE
    settings.TELNYX_REQUIRE_SIGNATURE = True
    response = client.post("/api/comms/webhooks/telnyx", json={"data": {"event_type": "call.initiated"}})
    settings.TELNYX_REQUIRE_SIGNATURE = original
    assert response.status_code == 401
