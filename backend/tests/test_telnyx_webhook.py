from core.config import settings


def _auth_headers(client, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{role}@example.com",
            "full_name": "Comms User",
            "password": "securepass",
            "role": role,
            "organization_name": "TestOrg",
        },
    )
    payload = response.json()
    token = payload["access_token"]
    org_id = payload.get("user", {}).get("org_id")
    return {"Authorization": f"Bearer {token}"}, org_id


def test_telnyx_webhook_creates_call_log_and_event(client):
    headers, org_id = _auth_headers(client, role="admin")
    payload = {
        "data": {
            "id": "evt-1",
            "event_type": "call.initiated",
            "occurred_at": "2024-01-01T01:00:00Z",
            "payload": {
                "call_control_id": "call-123",
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

    response = client.get("/api/comms/calls", headers=headers)
    assert response.status_code == 200
    calls = response.json()
    assert any(call.get("external_call_id") == "call-123" for call in calls)

    response = client.get("/api/comms/calls/call-123/timeline", headers=headers)
    assert response.status_code == 200
    timeline = response.json()
    assert timeline


def test_telnyx_signature_enforced_when_enabled(client):
    original = settings.TELNYX_REQUIRE_SIGNATURE
    settings.TELNYX_REQUIRE_SIGNATURE = True
    response = client.post("/api/comms/webhooks/telnyx", json={"data": {"event_type": "call.initiated"}})
    settings.TELNYX_REQUIRE_SIGNATURE = original
    assert response.status_code == 401
