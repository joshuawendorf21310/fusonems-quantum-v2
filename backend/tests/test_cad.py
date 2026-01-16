
def _register_user(client, email, org_name, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "CAD User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="dispatcher"):
    headers, _ = _register_user(client, f"{role}@example.com", "TestOrg", role=role)
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


def test_create_call_and_unit(client):
    headers = _auth_headers(client)

    call_payload = {
        "caller_name": "Test Caller",
        "caller_phone": "555-1234",
        "location_address": "100 Main St",
        "latitude": 40.0,
        "longitude": -74.0,
        "priority": "High",
    }
    response = client.post("/api/cad/calls", json=call_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "cad.call.created")
    assert _has_audit(audits, "cad_call")

    unit_payload = {
        "unit_identifier": "A-1",
        "status": "Available",
        "latitude": 40.1,
        "longitude": -74.1,
    }
    response = client.post("/api/cad/units", json=unit_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "cad.unit.created")
    assert _has_audit(audits, "cad_unit")

    response = client.get("/api/cad/units", headers=headers)
    assert response.status_code == 200
    assert response.json()["active_units"]


def test_cad_cross_org_denied(client):
    headers_a, _ = _register_user(client, "cad_a@example.com", "CadOrgA", role="dispatcher")
    call_payload = {
        "caller_name": "Caller A",
        "caller_phone": "555-1000",
        "location_address": "1 A St",
        "latitude": 40.0,
        "longitude": -74.0,
        "priority": "High",
    }
    response = client.post("/api/cad/calls", json=call_payload, headers=headers_a)
    assert response.status_code == 201
    call_id = response.json()["id"]

    headers_b, _ = _register_user(client, "cad_b@example.com", "CadOrgB", role="dispatcher")
    unit_payload = {
        "unit_identifier": "B-1",
        "status": "Available",
        "latitude": 40.1,
        "longitude": -74.1,
    }
    response = client.post("/api/cad/units", json=unit_payload, headers=headers_b)
    assert response.status_code == 201

    response = client.post(
        "/api/cad/dispatch",
        json={"call_id": call_id, "unit_identifier": "B-1"},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_cad_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    call_payload = {
        "caller_name": "Caller B",
        "caller_phone": "555-1001",
        "location_address": "2 B St",
        "latitude": 41.0,
        "longitude": -75.0,
        "priority": "Routine",
    }
    response = client.post("/api/cad/calls", json=call_payload, headers=headers)
    assert response.status_code == 403
