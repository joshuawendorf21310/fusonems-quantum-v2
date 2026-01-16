def _register_user(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Batch Ten User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="admin"):
    headers, _ = _register_user(client, f"{role}@example.com", "BatchTenOrg", role=role)
    return headers


def _list_events(client, headers):
    response = client.get("/api/events", headers=headers)
    assert response.status_code == 200
    return response.json()


def _list_audits(client, headers):
    response = client.get("/api/compliance/forensic", headers=headers)
    assert response.status_code == 200
    return response.json()


def _has_event(events, event_type):
    return any(event.get("event_type") == event_type for event in events)


def _has_audit(audits, resource, action="create"):
    return any(
        audit.get("resource") == resource and audit.get("action") == action for audit in audits
    )


def test_auth_device_system_training_events(client):
    headers, user_id = _register_user(client, "core_admin@example.com", "CoreOrg", role="admin")
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "auth.organization.created")
    assert _has_event(events, "auth.user.registered")
    assert _has_audit(audits, "organization")
    assert _has_audit(audits, "user")

    response = client.post(
        "/api/auth/devices",
        json={"device_id": "dev-001", "fingerprint": "fp-001"},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "auth.device.enrolled")
    assert _has_audit(audits, "device_trust")

    response = client.post("/api/auth/devices/dev-001/approve", headers=headers)
    assert response.status_code == 200
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "auth.device.approved")
    assert _has_audit(audits, "device_trust", action="update")

    response = client.get("/api/system/modules", headers=headers)
    assert response.status_code == 200
    module_key = response.json()[0]["module_key"]
    response = client.patch(
        f"/api/system/modules/{module_key}",
        json={"enabled": False},
        headers=headers,
    )
    assert response.status_code == 200
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "system.module.updated")
    assert _has_audit(audits, "module_registry", action="update")

    response = client.post("/api/training/org", json={"enabled": True}, headers=headers)
    assert response.status_code == 200
    response = client.post(
        "/api/training/user",
        json={"user_id": user_id, "enabled": True},
        headers=headers,
    )
    assert response.status_code == 200

    response = client.post("/api/training/seed", headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    assert _has_event(events, "training.org_mode.updated")
    assert _has_event(events, "training.user_mode.updated")
    assert _has_event(events, "cad.call.created")
    assert _has_event(events, "epcr.patient.created")
    assert _has_event(events, "schedule.shift.created")
    assert _has_event(events, "billing.invoice.created")
    assert _has_event(events, "ai_console.insight.created")

    response = client.post("/api/events", json={"event_type": "RUN_CREATED", "payload": {}}, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    assert _has_event(events, "events.published")
    assert _has_event(events, "RUN_CREATED")


def test_core_cross_org_isolation(client):
    headers_a, _ = _register_user(client, "core_a@example.com", "CoreOrgA", role="admin")
    response = client.post(
        "/api/auth/devices",
        json={"device_id": "dev-a", "fingerprint": "fp-a"},
        headers=headers_a,
    )
    assert response.status_code == 201
    response = client.post(
        "/api/events",
        json={"event_type": "CORE_EVENT", "payload": {}},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "core_b@example.com", "CoreOrgB", role="admin")
    response = client.get("/api/auth/devices", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()

    response = client.get("/api/events", headers=headers_b)
    assert response.status_code == 200
    assert not _has_event(response.json(), "CORE_EVENT")


def test_core_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.patch("/api/system/modules/unknown", json={"enabled": True}, headers=headers)
    assert response.status_code == 403

    response = client.post("/api/training/org", json={"enabled": True}, headers=headers)
    assert response.status_code == 403

    response = client.post("/api/auth/devices/dev-1/approve", headers=headers)
    assert response.status_code == 403

    response = client.post("/api/events/replay", json={}, headers=headers)
    assert response.status_code == 403
