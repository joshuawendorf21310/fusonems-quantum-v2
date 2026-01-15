def _auth_headers(client, role="provider"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{role}@example.com",
            "full_name": "Validation User",
            "password": "securepass",
            "role": role,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_validation_scan(client):
    headers = _auth_headers(client)
    payload = {
        "entity_type": "epcr",
        "entity_id": "INC-1001",
        "patient_name": "",
        "date_of_birth": None,
        "insurance_id": "",
        "encounter_code": "",
        "claim_amount": -1,
    }
    response = client.post("/api/validation/scan", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["count"] > 0
