def _register(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Tenant User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_cross_tenant_isolation_across_modules(client):
    org_a = _register(client, "ops-a@example.com", "OrgAlpha", role="admin")
    org_b = _register(client, "ops-b@example.com", "OrgBravo", role="admin")

    response = client.post(
        "/api/comms/threads",
        json={"channel": "sms", "subject": "Ops", "participants": ["Unit 1"]},
        headers=org_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/inventory/items",
        json={"name": "Trauma Kit", "quantity_on_hand": 1, "location": "Station 1"},
        headers=org_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/fire/incidents",
        json={"incident_type": "structure", "location": "Main St"},
        headers=org_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/legal-portal/cases",
        json={"case_number": "LEGAL-ORG-A"},
        headers=org_a,
    )
    assert response.status_code == 201

    response = client.post(
        "/api/training-center/courses",
        json={"title": "EMS Compliance", "credit_hours": 1},
        headers=org_a,
    )
    assert response.status_code == 201

    response = client.get("/api/comms/threads", headers=org_b)
    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/api/inventory/items", headers=org_b)
    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/api/fire/incidents", headers=org_b)
    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/api/legal-portal/cases", headers=org_b)
    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/api/training-center/courses", headers=org_b)
    assert response.status_code == 200
    assert response.json() == []
