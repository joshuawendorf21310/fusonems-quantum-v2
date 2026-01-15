
def _auth_headers(client, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{role}@example.com",
            "full_name": "CAD User",
            "password": "securepass",
            "role": role,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_call_and_unit(client):
    headers = _auth_headers(client)

    call_payload = {
        "caller_name": "Test Caller",
        "caller_phone": "555-1234",
        "location_address": "100 Main St",
        "latitude": 40.0,
        "longitude": -74.0,
        "priority": "High",
    }
    response = client.post("/api/cad/calls", json=call_payload, headers=headers)
    assert response.status_code == 201

    unit_payload = {
        "unit_identifier": "A-1",
        "status": "Available",
        "latitude": 40.1,
        "longitude": -74.1,
    }
    response = client.post("/api/cad/units", json=unit_payload, headers=headers)
    assert response.status_code == 201

    response = client.get("/api/cad/units")
    assert response.status_code == 200
    assert response.json()["active_units"]
