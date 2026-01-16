def _register_user(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Batch Nine User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="admin"):
    headers, _ = _register_user(client, f"{role}@example.com", "BatchNineOrg", role=role)
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


def test_ops_console_business_founder_investor_schedule_mail(client):
    headers = _auth_headers(client, role="admin")

    response = client.post(
        "/api/ai_console/insights",
        json={"category": "ops", "prompt": "Need", "response": "Ok", "metrics": {}},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "ai_console.insight.created")
    assert _has_audit(audits, "ai_insight")

    response = client.post(
        "/api/ai_console/explain",
        json={"decision_packet": {"decision": "allow"}, "audience": "ops"},
        headers=headers,
    )
    assert response.status_code == 200
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "ai_console.explanation.created")
    assert _has_audit(audits, "ai_explanation", action="explain")

    response = client.post(
        "/api/business-ops/tasks",
        json={"title": "Renew contract", "owner": "Ops", "priority": "High"},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "business_ops.task.created")
    assert _has_audit(audits, "business_ops_task")

    response = client.post(
        "/api/founder/metrics",
        json={"category": "Growth", "value": "20%", "details": {"q": "Q1"}},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "founder.metric.created")
    assert _has_audit(audits, "founder_metric")

    response = client.post(
        "/api/investor_demo/metrics",
        json={"name": "ARR", "value": "$1M", "context": {"period": "Q2"}},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "investor.metric.created")
    assert _has_audit(audits, "investor_metric")

    response = client.post(
        "/api/mail/messages",
        json={"channel": "email", "recipient": "ops@example.com", "body": "Update"},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "mail.message.created")
    assert _has_audit(audits, "mail_message")

    response = client.post(
        "/api/schedule/shifts",
        json={
            "crew_name": "Crew A",
            "shift_start": "2026-01-16T08:00:00Z",
            "shift_end": "2026-01-16T20:00:00Z",
            "status": "Scheduled",
            "certifications": ["BLS"],
        },
        headers=headers,
    )
    assert response.status_code == 201
    shift_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "schedule.shift.created")
    assert _has_audit(audits, "schedule_shift")

    response = client.post(
        f"/api/schedule/shifts/{shift_id}/swap?new_crew=Crew+B",
        headers=headers,
    )
    assert response.status_code == 200
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "schedule.shift.updated")
    assert _has_audit(audits, "schedule_shift", action="update")


def test_ops_cross_org_denied(client):
    headers_a, _ = _register_user(client, "ops_a@example.com", "OpsOrgA", role="admin")
    response = client.post(
        "/api/ai_console/insights",
        json={"category": "ops", "prompt": "A", "response": "B", "metrics": {}},
        headers=headers_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/business-ops/tasks",
        json={"title": "Task A", "owner": "Ops", "priority": "Low"},
        headers=headers_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/founder/metrics",
        json={"category": "Retention", "value": "90%", "details": {}},
        headers=headers_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/investor_demo/metrics",
        json={"name": "LTV", "value": "$5000", "context": {}},
        headers=headers_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/mail/messages",
        json={"channel": "email", "recipient": "ops@example.com", "body": "Cross org"},
        headers=headers_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/schedule/shifts",
        json={
            "crew_name": "Crew X",
            "shift_start": "2026-01-16T08:00:00Z",
            "shift_end": "2026-01-16T20:00:00Z",
            "status": "Scheduled",
            "certifications": ["BLS"],
        },
        headers=headers_a,
    )
    assert response.status_code == 201
    shift_id = response.json()["id"]

    headers_b, _ = _register_user(client, "ops_b@example.com", "OpsOrgB", role="admin")
    response = client.get("/api/ai_console/insights", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()

    response = client.get("/api/business-ops/tasks", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()

    response = client.get("/api/founder/metrics", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()

    response = client.get("/api/investor_demo/metrics", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()

    response = client.get("/api/mail/messages", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()

    response = client.post(
        f"/api/schedule/shifts/{shift_id}/swap?new_crew=Crew+Z",
        headers=headers_b,
    )
    assert response.status_code == 403


def test_ops_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/ai_console/insights",
        json={"category": "ops", "prompt": "No", "response": "No", "metrics": {}},
        headers=headers,
    )
    assert response.status_code == 403

    response = client.post(
        "/api/business-ops/tasks",
        json={"title": "Forbidden", "owner": "Ops", "priority": "High"},
        headers=headers,
    )
    assert response.status_code == 403

    response = client.post(
        "/api/founder/metrics",
        json={"category": "Ops", "value": "0", "details": {}},
        headers=headers,
    )
    assert response.status_code == 403

    response = client.post(
        "/api/investor_demo/metrics",
        json={"name": "GMV", "value": "$0", "context": {}},
        headers=headers,
    )
    assert response.status_code == 403

    response = client.post(
        "/api/mail/messages",
        json={"channel": "email", "recipient": "blocked@example.com", "body": "Denied"},
        headers=headers,
    )
    assert response.status_code == 403

    response = client.post(
        "/api/schedule/shifts",
        json={
            "crew_name": "Crew Denied",
            "shift_start": "2026-01-16T08:00:00Z",
            "shift_end": "2026-01-16T20:00:00Z",
            "status": "Scheduled",
            "certifications": ["BLS"],
        },
        headers=headers,
    )
    assert response.status_code == 403
