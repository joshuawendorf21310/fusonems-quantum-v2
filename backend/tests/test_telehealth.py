def _auth_headers(client, role="provider"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{role}@example.com",
            "full_name": "Telehealth User",
            "password": "securepass",
            "role": role,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_telehealth_session(client):
    headers = _auth_headers(client)
    payload = {"title": "Telehealth Intake", "host_name": "Dr. Skylar"}
    response = client.post("/api/telehealth/sessions", json=payload, headers=headers)
    assert response.status_code == 201
    session_uuid = response.json()["session_uuid"]

    response = client.post(
        f"/api/telehealth/sessions/{session_uuid}/participants",
        json={"name": "Patient One", "role": "patient"},
        headers=headers,
    )
    assert response.status_code == 201
