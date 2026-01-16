def _register_user(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Batch Eleven User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="admin"):
    headers, _ = _register_user(client, f"{role}@example.com", "BatchElevenOrg", role=role)
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


def test_legal_hold_flow(client):
    admin_headers, _ = _register_user(
        client, "legal_admin@example.com", "LegalOrgCore", role="admin"
    )
    medical_headers, _ = _register_user(
        client, "legal_md@example.com", "LegalOrgCore", role="medical_director"
    )

    response = client.post(
        "/api/legal-hold",
        json={"scope_type": "epcr_patient", "scope_id": "LEGAL-100", "reason": "Hold"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    holds = client.get("/api/legal-hold", headers=admin_headers).json()
    hold_id = holds[0]["id"]
    events = _list_events(client, admin_headers)
    audits = _list_audits(client, admin_headers)
    assert _has_event(events, "legal_hold.created")
    assert _has_audit(audits, "legal_hold")

    response = client.post(
        "/api/legal-hold/addenda",
        json={"resource_type": "epcr_patient", "resource_id": "LEGAL-100", "note": "Note"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    events = _list_events(client, admin_headers)
    audits = _list_audits(client, admin_headers)
    assert _has_event(events, "legal_hold.addendum.created")
    assert _has_audit(audits, "addendum", action="addendum")

    response = client.post(
        "/api/legal-hold/overrides",
        json={
            "override_type": "release",
            "resource_type": "epcr_patient",
            "resource_id": "LEGAL-100",
            "reason_code": "QA_OVERRIDE",
        },
        headers=medical_headers,
    )
    assert response.status_code == 201
    override_id = response.json()["id"]
    events = _list_events(client, medical_headers)
    audits = _list_audits(client, medical_headers)
    assert _has_event(events, "legal_hold.override.created")
    assert _has_audit(audits, "override_request")

    response = client.post(
        f"/api/legal-hold/overrides/{override_id}/approve",
        headers=medical_headers,
    )
    assert response.status_code == 200
    events = _list_events(client, medical_headers)
    audits = _list_audits(client, medical_headers)
    assert _has_event(events, "legal_hold.override.approved")
    assert _has_audit(audits, "override_request", action="approve")

    response = client.post(f"/api/legal-hold/{hold_id}/release", headers=admin_headers)
    assert response.status_code == 200
    events = _list_events(client, admin_headers)
    audits = _list_audits(client, admin_headers)
    assert _has_event(events, "legal_hold.released")
    assert _has_audit(audits, "legal_hold", action="release")


def test_legal_cross_org_denied(client):
    headers_a, _ = _register_user(client, "legal_a@example.com", "LegalOrgA", role="admin")
    response = client.post(
        "/api/legal-hold",
        json={"scope_type": "epcr_patient", "scope_id": "LEGAL-200", "reason": "Hold"},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "legal_b@example.com", "LegalOrgB", role="admin")
    response = client.get("/api/legal-hold", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()

    response = client.get(
        "/api/legal-hold/addenda",
        params={"resource_type": "epcr_patient", "resource_id": "LEGAL-200"},
        headers=headers_b,
    )
    assert response.status_code == 200
    assert not response.json()


def test_legal_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/legal-hold",
        json={"scope_type": "epcr_patient", "scope_id": "LEGAL-403", "reason": "Denied"},
        headers=headers,
    )
    assert response.status_code == 403

    response = client.post(
        "/api/legal-hold/overrides",
        json={
            "override_type": "release",
            "resource_type": "epcr_patient",
            "resource_id": "LEGAL-403",
            "reason_code": "DENIED",
        },
        headers=headers,
    )
    assert response.status_code == 403
