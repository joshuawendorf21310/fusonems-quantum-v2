
def _register_user(client, email, org_name, role="provider"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Provider User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="provider"):
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


def test_create_patient(client):
    headers = _auth_headers(client)
    payload = {
        "first_name": "Riley",
        "last_name": "Morgan",
        "date_of_birth": "1990-01-01",
        "incident_number": "INC-1000",
        "vitals": {"bp": "120/80"},
        "interventions": ["Oxygen"],
        "medications": ["Aspirin"],
        "procedures": ["IV"],
    }
    response = client.post("/api/epcr/patients", json=payload, headers=headers)
    assert response.status_code == 201
    patient_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "epcr.patient.created")
    assert _has_audit(audits, "epcr_patient")

    response = client.get(f"/api/epcr/patients/{patient_id}", headers=headers)
    assert response.status_code == 200


def test_epcr_cross_org_denied(client):
    headers_a, _ = _register_user(client, "epcr_a@example.com", "EpcrOrgA", role="provider")
    payload = {
        "first_name": "Taylor",
        "last_name": "Reed",
        "date_of_birth": "1985-02-02",
        "incident_number": "INC-2000",
    }
    response = client.post("/api/epcr/patients", json=payload, headers=headers_a)
    assert response.status_code == 201
    patient_id = response.json()["id"]

    headers_b, _ = _register_user(client, "epcr_b@example.com", "EpcrOrgB", role="provider")
    response = client.get(f"/api/epcr/patients/{patient_id}", headers=headers_b)
    assert response.status_code == 403


def test_epcr_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    payload = {
        "first_name": "Jamie",
        "last_name": "Lee",
        "date_of_birth": "1992-03-03",
        "incident_number": "INC-3000",
    }
    response = client.post("/api/epcr/patients", json=payload, headers=headers)
    assert response.status_code == 403
