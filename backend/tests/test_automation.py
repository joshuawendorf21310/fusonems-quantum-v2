def _auth_headers(client, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{role}@example.com",
            "full_name": "Automation User",
            "password": "securepass",
            "role": role,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_rule_and_task(client):
    headers = _auth_headers(client)
    rule_payload = {"name": "Missing ePCR", "trigger": "epcr.incomplete", "action": "notify"}
    response = client.post("/api/automation/rules", json=rule_payload, headers=headers)
    assert response.status_code == 201

    task_payload = {"title": "Follow-up patient", "owner": "Team A", "priority": "High"}
    response = client.post("/api/automation/tasks", json=task_payload, headers=headers)
    assert response.status_code == 201
