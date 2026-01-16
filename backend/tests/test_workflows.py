def _register_user(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Workflow User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="admin"):
    headers, _ = _register_user(client, f"{role}@workflow.example.com", "WorkflowOrg", role=role)
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


def test_workflow_lifecycle(client):
    headers = _auth_headers(client)
    payload = {
        "workflow_key": "hems_mission_acceptance",
        "resource_type": "hems_mission",
        "resource_id": "101",
        "status": "started",
        "last_step": "intake",
    }
    response = client.post("/api/workflows", json=payload, headers=headers)
    assert response.status_code == 201
    workflow_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "workflows.created")
    assert _has_audit(audits, "workflow_state")

    response = client.post(
        f"/api/workflows/{workflow_id}/status",
        json={"status": "interrupted", "last_step": "dispatch"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "workflows.updated")
    assert _has_audit(audits, "workflow_state", action="update")

    response = client.post(f"/api/workflows/{workflow_id}/resume", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "workflows.resumed")
    assert _has_audit(audits, "workflow_state", action="resume")


def test_workflows_cross_org_denied(client):
    headers_a, _ = _register_user(client, "wf_a@example.com", "WfOrgA", role="admin")
    response = client.post(
        "/api/workflows",
        json={"workflow_key": "wfa", "resource_type": "cad_call", "resource_id": "100"},
        headers=headers_a,
    )
    assert response.status_code == 201
    workflow_id = response.json()["id"]

    headers_b, _ = _register_user(client, "wf_b@example.com", "WfOrgB", role="admin")
    response = client.post(
        f"/api/workflows/{workflow_id}/resume",
        headers=headers_b,
    )
    assert response.status_code == 403


def test_workflows_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/workflows",
        json={"workflow_key": "wfb", "resource_type": "cad_call", "resource_id": "200"},
        headers=headers,
    )
    assert response.status_code == 403
