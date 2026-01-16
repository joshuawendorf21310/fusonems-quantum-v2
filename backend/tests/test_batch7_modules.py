
def _register_user(client, email, org_name, role="founder"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Batch Seven User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="founder"):
    headers, _ = _register_user(client, f"{role}@example.com", "BatchSevenOrg", role=role)
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


def test_founder_ops(client):
    headers = _auth_headers(client, role="founder")
    response = client.post(
        "/api/founder-ops/pwa",
        json={"platform": "web", "current_version": "2.4.0"},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "founder_ops.pwa.created")
    assert _has_audit(audits, "pwa_distribution")

    response = client.post(
        "/api/founder-ops/pricing",
        json={"plan_name": "Enterprise"},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "founder_ops.pricing.created")
    assert _has_audit(audits, "pricing_plan")

    response = client.post(
        "/api/founder-ops/incidents",
        json={"title": "Latency spike"},
        headers=headers,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/founder-ops/governance",
        json={"rule_type": "retention"},
        headers=headers,
    )
    assert response.status_code == 201


def test_founder_ops_cross_org_denied(client):
    headers_a, _ = _register_user(client, "founder_a@example.com", "FounderOrgA", role="founder")
    response = client.post(
        "/api/founder-ops/pwa",
        json={"platform": "web", "current_version": "2.5.0"},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "founder_b@example.com", "FounderOrgB", role="founder")
    response = client.get("/api/founder-ops/pwa", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_founder_ops_rbac_denied(client):
    headers = _auth_headers(client, role="admin")
    response = client.post(
        "/api/founder-ops/pwa",
        json={"platform": "web", "current_version": "2.6.0"},
        headers=headers,
    )
    assert response.status_code == 403


def test_legal_and_patient_portals(client):
    headers = _auth_headers(client, role="admin")
    case_payload = {"case_number": "LEGAL-001"}
    response = client.post("/api/legal-portal/cases", json=case_payload, headers=headers)
    assert response.status_code == 201
    case_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "legal_portal.case.created")
    assert _has_audit(audits, "legal_case")

    evidence_payload = {"case_id": case_id, "evidence_type": "document"}
    response = client.post("/api/legal-portal/evidence", json=evidence_payload, headers=headers)
    assert response.status_code == 201

    account_payload = {"patient_name": "Riley Morgan", "email": "riley@example.com"}
    response = client.post("/api/patient-portal/accounts", json=account_payload, headers=headers)
    assert response.status_code == 201
    account_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "patient_portal.account.created")
    assert _has_audit(audits, "patient_portal_account")

    message_payload = {"account_id": account_id, "message": "Need billing copy"}
    response = client.post("/api/patient-portal/messages", json=message_payload, headers=headers)
    assert response.status_code == 201


def test_legal_portal_cross_org_denied(client):
    headers_a, _ = _register_user(client, "legal_a@example.com", "LegalOrgA", role="admin")
    response = client.post(
        "/api/legal-portal/cases", json={"case_number": "LEGAL-101"}, headers=headers_a
    )
    assert response.status_code == 201
    case_id = response.json()["id"]

    headers_b, _ = _register_user(client, "legal_b@example.com", "LegalOrgB", role="admin")
    response = client.post(
        "/api/legal-portal/evidence",
        json={"case_id": case_id, "evidence_type": "record"},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_legal_portal_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/legal-portal/cases",
        json={"case_number": "LEGAL-403"},
        headers=headers,
    )
    assert response.status_code == 403


def test_patient_portal_cross_org_denied(client):
    headers_a, _ = _register_user(client, "patient_a@example.com", "PatientOrgA", role="admin")
    response = client.post(
        "/api/patient-portal/accounts",
        json={"patient_name": "Alex", "email": "alex@example.com"},
        headers=headers_a,
    )
    assert response.status_code == 201
    account_id = response.json()["id"]

    headers_b, _ = _register_user(client, "patient_b@example.com", "PatientOrgB", role="admin")
    response = client.post(
        "/api/patient-portal/messages",
        json={"account_id": account_id, "message": "Cross org"},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_patient_portal_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post(
        "/api/patient-portal/accounts",
        json={"patient_name": "Morgan", "email": "morgan@example.com"},
        headers=headers,
    )
    assert response.status_code == 403
