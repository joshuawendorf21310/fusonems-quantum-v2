def _auth_headers(client, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{role}@example.com",
            "full_name": "Compliance User",
            "password": "securepass",
            "role": role,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_alert_and_audit(client):
    headers = _auth_headers(client)
    alert_payload = {
        "category": "HIPAA",
        "severity": "High",
        "message": "Unauthorized access attempt detected",
    }
    response = client.post("/api/compliance/alerts", json=alert_payload, headers=headers)
    assert response.status_code == 201

    audit_payload = {
        "user_email": "user@example.com",
        "action": "read",
        "resource": "epcr:INC-1002",
        "outcome": "Allowed",
    }
    response = client.post("/api/compliance/audits", json=audit_payload, headers=headers)
    assert response.status_code == 201
