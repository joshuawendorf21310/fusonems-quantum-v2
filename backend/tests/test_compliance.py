def _register_user(client, email, org_name, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Compliance User",
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


def test_create_alert_and_audit(client):
    headers = _auth_headers(client)
    alert_payload = {
        "category": "HIPAA",
        "severity": "High",
        "message": "Unauthorized access attempt detected",
    }
    response = client.post("/api/compliance/alerts", json=alert_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "compliance.alert.created")
    assert _has_audit(audits, "compliance_alert")

    audit_payload = {
        "user_email": "user@example.com",
        "action": "read",
        "resource": "epcr:INC-1002",
        "outcome": "Allowed",
    }
    response = client.post("/api/compliance/audits", json=audit_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "compliance.audit.created")
    assert _has_audit(audits, "access_audit")


def test_compliance_cross_org_denied(client):
    headers_a, _ = _register_user(client, "comp_a@example.com", "CompOrgA", role="dispatcher")
    response = client.post(
        "/api/compliance/alerts",
        json={"category": "HIPAA", "severity": "High", "message": "OrgA alert"},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "comp_b@example.com", "CompOrgB", role="dispatcher")
    response = client.get("/api/compliance/alerts", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_compliance_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/compliance/alerts",
        json={"category": "HIPAA", "severity": "High", "message": "Denied"},
        headers=headers,
    )
    assert response.status_code == 403
