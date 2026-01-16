def _register_user(client, email, org_name, role="provider"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Consent User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="provider"):
    headers, _ = _register_user(client, f"{role}@consent.example.com", "ConsentOrg", role=role)
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


def test_consent_provenance_create_and_list(client):
    headers = _auth_headers(client)
    payload = {
        "subject_type": "telehealth_session",
        "subject_id": "session-123",
        "policy_hash": "policy-v1",
        "context": "telehealth_intake",
        "metadata": {"accepted": True},
    }
    response = client.post("/api/consent", json=payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "consent.created")
    assert _has_audit(audits, "consent_provenance")

    response = client.get(
        "/api/consent?subject_type=telehealth_session&subject_id=session-123",
        headers=headers,
    )
    assert response.status_code == 200
    records = response.json()
    assert records


def test_consent_cross_org_denied(client):
    headers_a, _ = _register_user(client, "consent_a@example.com", "ConsentOrgA", role="provider")
    response = client.post(
        "/api/consent",
        json={
            "subject_type": "telehealth_session",
            "subject_id": "session-999",
            "policy_hash": "policy-v1",
        },
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "consent_b@example.com", "ConsentOrgB", role="provider")
    response = client.get("/api/consent?subject_type=telehealth_session", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_consent_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post(
        "/api/consent",
        json={"subject_type": "telehealth_session", "subject_id": "session-000"},
        headers=headers,
    )
    assert response.status_code == 403
