def _register_user(client, email, org_name, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Automation User",
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


def test_create_rule_and_task(client):
    headers = _auth_headers(client)
    rule_payload = {"name": "Missing ePCR", "trigger": "epcr.incomplete", "action": "notify"}
    response = client.post("/api/automation/rules", json=rule_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "automation.rule.created")
    assert _has_audit(audits, "automation_rule")

    task_payload = {"title": "Follow-up patient", "owner": "Team A", "priority": "High"}
    response = client.post("/api/automation/tasks", json=task_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "automation.task.created")
    assert _has_audit(audits, "automation_task")


def test_automation_cross_org_denied(client):
    headers_a, _ = _register_user(client, "auto_a@example.com", "AutoOrgA", role="dispatcher")
    response = client.post(
        "/api/automation/rules",
        json={"name": "Rule A", "trigger": "event", "action": "notify"},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "auto_b@example.com", "AutoOrgB", role="dispatcher")
    response = client.get("/api/automation/rules", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_automation_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/automation/rules",
        json={"name": "Rule B", "trigger": "event", "action": "notify"},
        headers=headers,
    )
    assert response.status_code == 403
