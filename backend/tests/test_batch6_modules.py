
def _register_user(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Batch Six User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="admin"):
    headers, _ = _register_user(client, f"{role}@example.com", "BatchSixOrg", role=role)
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


def test_fire_exports(client):
    headers = _auth_headers(client, role="dispatcher")
    incident_payload = {"incident_type": "Structure", "location": "10 Main"}
    response = client.post("/api/fire/incidents", json=incident_payload, headers=headers)
    assert response.status_code == 201
    incident_id = response.json()["incident_id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "fire.incident.created")
    assert _has_audit(audits, "fire_incident")

    response = client.post(
        "/api/fire/exports/nfirs", json={"incident_id": incident_id}, headers=headers
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "fire.export.nfirs_created")
    assert _has_audit(audits, "fire_export")

    response = client.post(
        "/api/fire/exports/neris", json={"incident_id": incident_id}, headers=headers
    )
    assert response.status_code == 201


def test_fire_cross_org_denied(client):
    headers_a, _ = _register_user(client, "fire_a@example.com", "FireOrgA", role="dispatcher")
    response = client.post(
        "/api/fire/incidents",
        json={"incident_type": "Medical", "location": "22 Elm"},
        headers=headers_a,
    )
    assert response.status_code == 201
    incident_id = response.json()["incident_id"]

    headers_b, _ = _register_user(client, "fire_b@example.com", "FireOrgB", role="dispatcher")
    response = client.post(
        "/api/fire/exports/nfirs", json={"incident_id": incident_id}, headers=headers_b
    )
    assert response.status_code == 403


def test_fire_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/fire/incidents",
        json={"incident_type": "Rescue", "location": "99 Oak"},
        headers=headers,
    )
    assert response.status_code == 403


def test_hems_qa(client):
    headers = _auth_headers(client, role="hems_supervisor")
    mission_payload = {
        "mission_type": "scene",
        "requesting_party": "Ops",
        "pickup_location": "LZ",
        "destination_location": "Hospital",
    }
    response = client.post("/api/hems/missions", json=mission_payload, headers=headers)
    assert response.status_code == 201
    mission_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "hems.mission.created")
    assert _has_audit(audits, "hems_mission")

    qa_payload = {"mission_id": mission_id, "reviewer": "QA Lead", "notes": "Review"}
    response = client.post("/api/hems/qa", json=qa_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "hems.qa.created")
    assert _has_audit(audits, "hems_quality_review")


def test_hems_cross_org_denied(client):
    headers_a, _ = _register_user(client, "hems_a@example.com", "HemsOrgA", role="hems_supervisor")
    response = client.post(
        "/api/hems/missions",
        json={
            "mission_type": "scene",
            "requesting_party": "Ops",
            "pickup_location": "LZ",
            "destination_location": "Hospital",
        },
        headers=headers_a,
    )
    assert response.status_code == 201
    mission_id = response.json()["id"]

    headers_b, _ = _register_user(client, "hems_b@example.com", "HemsOrgB", role="hems_supervisor")
    response = client.post(
        "/api/hems/qa", json={"mission_id": mission_id, "reviewer": "QA"}, headers=headers_b
    )
    assert response.status_code == 403


def test_hems_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/hems/missions",
        json={
            "mission_type": "scene",
            "requesting_party": "Ops",
            "pickup_location": "LZ",
            "destination_location": "Hospital",
        },
        headers=headers,
    )
    assert response.status_code == 403


def test_telehealth_consent_and_token(client):
    headers = _auth_headers(client, role="provider")
    session_payload = {"title": "Telemed", "host_name": "Dr. Lee"}
    response = client.post("/api/telehealth/sessions", json=session_payload, headers=headers)
    assert response.status_code == 201
    session_uuid = response.json()["session_uuid"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "telehealth.session.created")
    assert _has_audit(audits, "telehealth_session")

    response = client.post(f"/api/telehealth/sessions/{session_uuid}/consent", headers=headers)
    assert response.status_code == 200
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "telehealth.consent.created")
    assert _has_audit(audits, "consent_provenance")

    response = client.get(
        f"/api/telehealth/sessions/{session_uuid}/secure-token", headers=headers
    )
    assert response.status_code == 200


def test_telehealth_cross_org_denied(client):
    headers_a, _ = _register_user(client, "tele_a@example.com", "TeleOrgA", role="provider")
    response = client.post(
        "/api/telehealth/sessions",
        json={"title": "Tele A", "host_name": "Dr. A"},
        headers=headers_a,
    )
    assert response.status_code == 201
    session_uuid = response.json()["session_uuid"]

    headers_b, _ = _register_user(client, "tele_b@example.com", "TeleOrgB", role="provider")
    response = client.get(
        f"/api/telehealth/sessions/{session_uuid}/secure-token", headers=headers_b
    )
    assert response.status_code == 403


def test_telehealth_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post(
        "/api/telehealth/sessions",
        json={"title": "Tele B", "host_name": "Dr. B"},
        headers=headers,
    )
    assert response.status_code == 403
