
def test_system_health_endpoint(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "founder@example.com",
            "full_name": "Founder",
            "password": "securepass",
            "role": "founder",
            "organization_name": "HealthOrg",
        },
    )
    token = response.json()["access_token"]
    response = client.get(
        "/api/system/health", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
    assert "upgrade" in payload
