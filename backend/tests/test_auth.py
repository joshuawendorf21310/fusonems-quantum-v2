
def test_register_and_login(client):
    register_payload = {
        "email": "dispatch@example.com",
        "full_name": "Dispatch Lead",
        "password": "securepass",
        "role": "dispatcher",
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    token = response.json()["access_token"]
    assert token

    login_payload = {
        "email": "dispatch@example.com",
        "password": "securepass",
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    assert response.json()["access_token"]
