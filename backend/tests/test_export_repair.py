def _register_user(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Export User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="admin"):
    headers, _ = _register_user(client, f"{role}@example.com", "ExportOrg", role=role)
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


def _has_audit(audits, resource, action="export"):
    return any(
        audit.get("resource") == resource and audit.get("action") == action for audit in audits
    )


def test_export_full(client):
    headers = _auth_headers(client, role="admin")
    response = client.post("/api/export/full", headers=headers)
    assert response.status_code == 201
    assert response.json()["export_hash"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "exports.full.created")
    assert _has_audit(audits, "data_export_manifest")


def test_export_cross_org_denied(client):
    headers_a, _ = _register_user(client, "export_a@example.com", "ExportOrgA", role="admin")
    response = client.post("/api/export/full", headers=headers_a)
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "export_b@example.com", "ExportOrgB", role="admin")
    response = client.get("/api/export/history", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_export_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post("/api/export/full", headers=headers)
    assert response.status_code == 403


def test_repair_scan(client):
    headers = _auth_headers(client, role="admin")
    response = client.get("/api/repair/scan", headers=headers)
    assert response.status_code == 200


def test_repair_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.get("/api/repair/scan", headers=headers)
    assert response.status_code == 403
