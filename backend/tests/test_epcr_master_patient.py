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


def _list_events(client, headers):
    response = client.get("/api/events", headers=headers)
    assert response.status_code == 200
    return response.json()


def _has_event(events, event_type):
    return any(event.get("event_type") == event_type for event in events)


def test_master_patient_link_and_repeat_candidates(client):
    headers, _ = _register_user(client, "mpi_provider@example.com", "MPI Org", role="provider")
    patient_payload = {
        "first_name": "Jordan",
        "last_name": "Smith",
        "date_of_birth": "1980-05-01",
        "phone": "555-555-0101",
        "address": "123 Main St",
        "incident_number": "INC-MPI-1",
    }
    patient_response = client.post("/api/epcr/patients", json=patient_payload, headers=headers)
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    master_payload = {
        "first_name": "Jordan",
        "last_name": "Smith",
        "date_of_birth": "1980-05-01",
        "phone": "555-555-0101",
        "address": "123 Main St",
    }
    master_response = client.post("/api/master_patients", json=master_payload, headers=headers)
    assert master_response.status_code == 201
    master_id = master_response.json()["id"]

    candidates_response = client.get(
        f"/api/epcr/patients/{patient_id}/repeat_candidates", headers=headers
    )
    assert candidates_response.status_code == 200
    candidates = candidates_response.json()
    assert any(candidate["master_patient_id"] == master_id for candidate in candidates)

    link_response = client.post(
        f"/api/epcr/patients/{patient_id}/link_master_patient",
        json={"master_patient_id": master_id, "provenance": "manual"},
        headers=headers,
    )
    assert link_response.status_code == 201
    events = _list_events(client, headers)
    assert _has_event(events, "epcr.master_patient.linked")


def test_master_patient_merge_and_isolation(client):
    headers_admin, _ = _register_user(client, "mpi_admin@example.com", "Merge Org", role="admin")
    master_a = client.post(
        "/api/master_patients",
        json={
            "first_name": "Casey",
            "last_name": "Lee",
            "date_of_birth": "1975-08-10",
        },
        headers=headers_admin,
    )
    master_b = client.post(
        "/api/master_patients",
        json={
            "first_name": "Casey",
            "last_name": "Lee",
            "date_of_birth": "1975-08-10",
        },
        headers=headers_admin,
    )
    assert master_a.status_code == 201
    assert master_b.status_code == 201

    merge_response = client.post(
        f"/api/master_patients/{master_a.json()['id']}/merge",
        json={"from_master_patient_id": master_b.json()["id"], "reason": "Duplicate"},
        headers=headers_admin,
    )
    assert merge_response.status_code == 201
    events = _list_events(client, headers_admin)
    assert _has_event(events, "epcr.master_patient.merged")

    headers_other, _ = _register_user(client, "mpi_other@example.com", "Other Org", role="provider")
    cross_response = client.get(
        f"/api/master_patients/{master_a.json()['id']}",
        headers=headers_other,
    )
    assert cross_response.status_code == 403
