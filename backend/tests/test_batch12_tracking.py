def _register_user(client, email, org_name, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Batch Twelve User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="dispatcher"):
    headers, _ = _register_user(client, f"{role}@example.com", "BatchTwelveOrg", role=role)
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


def _has_audit(audits, resource, action="update"):
    return any(
        audit.get("resource") == resource and audit.get("action") == action for audit in audits
    )


def test_tracking_updates_and_audits(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post(
        "/api/cad/track",
        json={"unit_id": "A1", "lat": 40.0, "lon": -75.0},
        headers=headers,
    )
    assert response.status_code == 200

    response = client.get("/api/cad/track", headers=headers)
    assert response.status_code == 200
    assert response.json()["A1"]["lat"] == 40.0

    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "cad.tracking.updated")
    assert _has_audit(audits, "cad_tracking")


def test_tracking_cross_org_isolation(client):
    headers_a, _ = _register_user(client, "track_a@example.com", "TrackOrgA", role="dispatcher")
    response = client.post(
        "/api/cad/track",
        json={"unit_id": "B2", "lat": 39.1, "lon": -76.1},
        headers=headers_a,
    )
    assert response.status_code == 200

    headers_b, _ = _register_user(client, "track_b@example.com", "TrackOrgB", role="dispatcher")
    response = client.get("/api/cad/track", headers=headers_b)
    assert response.status_code == 200
    assert "B2" not in response.json()


def test_tracking_rbac_denied(client):
    headers = _auth_headers(client, role="billing")
    response = client.post(
        "/api/cad/track",
        json={"unit_id": "X1", "lat": 40.1, "lon": -75.2},
        headers=headers,
    )
    assert response.status_code == 403
