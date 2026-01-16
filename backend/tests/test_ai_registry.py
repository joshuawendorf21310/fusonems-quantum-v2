def _register_user(client, email, org_name, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "AI User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="dispatcher"):
    headers, _ = _register_user(client, f"{role}@example.com", "AIOrg", role=role)
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


def test_ai_registry_create_and_replay(client):
    headers = _auth_headers(client, role="dispatcher")
    payload = {
        "model_name": "quantum-ai",
        "model_version": "v1",
        "prompt": "test prompt",
        "output_text": "AI advisory output",
        "advisory_level": "ADVISORY",
        "classification": "OPS",
        "input_refs": [{"resource": "test", "id": "1"}],
        "config_snapshot": {"temperature": 0},
    }
    response = client.post("/api/ai-registry", json=payload, headers=headers)
    assert response.status_code == 201
    output_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "ai_registry.output.created")
    assert _has_audit(audits, "ai_output")

    response = client.get(f"/api/ai-registry/{output_id}/replay", headers=headers)
    assert response.status_code == 200
    assert response.json()["output_id"] == output_id


def test_ai_registry_cross_org_denied(client):
    headers_a, _ = _register_user(client, "ai_a@example.com", "AiOrgA", role="dispatcher")
    payload = {
        "model_name": "quantum-ai",
        "model_version": "v1",
        "prompt": "test prompt",
        "output_text": "AI advisory output",
        "advisory_level": "ADVISORY",
        "classification": "OPS",
    }
    response = client.post("/api/ai-registry", json=payload, headers=headers_a)
    assert response.status_code == 201
    output_id = response.json()["id"]

    headers_b, _ = _register_user(client, "ai_b@example.com", "AiOrgB", role="dispatcher")
    response = client.get(f"/api/ai-registry/{output_id}/replay", headers=headers_b)
    assert response.status_code == 403


def test_ai_registry_rbac_denied(client):
    headers = _auth_headers(client, role="billing")
    payload = {
        "model_name": "quantum-ai",
        "model_version": "v1",
        "prompt": "test prompt",
        "output_text": "AI advisory output",
        "advisory_level": "ADVISORY",
        "classification": "OPS",
    }
    response = client.post("/api/ai-registry", json=payload, headers=headers)
    assert response.status_code == 403
