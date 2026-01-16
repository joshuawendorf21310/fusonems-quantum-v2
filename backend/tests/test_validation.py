def _register_user(client, email, org_name, role="provider"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Validation User",
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


def test_validation_scan(client):
    headers = _auth_headers(client)
    payload = {
        "entity_type": "epcr",
        "entity_id": "INC-1001",
        "patient_name": "",
        "date_of_birth": None,
        "insurance_id": "",
        "encounter_code": "",
        "claim_amount": -1,
    }
    response = client.post("/api/validation/scan", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["count"] > 0
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "validation.issue.created")
    assert _has_audit(audits, "validation_issue")


def test_validation_cross_org_denied(client):
    headers_a, _ = _register_user(client, "val_a@example.com", "ValOrgA", role="provider")
    response = client.post(
        "/api/validation/scan",
        json={"entity_type": "epcr", "entity_id": "INC-2001"},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "val_b@example.com", "ValOrgB", role="provider")
    response = client.get("/api/validation/issues", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_validation_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post(
        "/api/validation/rules",
        json={"name": "Rule X", "entity_type": "epcr"},
        headers=headers,
    )
    assert response.status_code == 403
