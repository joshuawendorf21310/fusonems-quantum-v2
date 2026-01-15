
def _auth_headers(client, role="provider"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{role}@example.com",
            "full_name": "Provider User",
            "password": "securepass",
            "role": role,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_patient(client):
    headers = _auth_headers(client)
    payload = {
        "first_name": "Riley",
        "last_name": "Morgan",
        "date_of_birth": "1990-01-01",
        "incident_number": "INC-1000",
        "vitals": {"bp": "120/80"},
        "interventions": ["Oxygen"],
        "medications": ["Aspirin"],
        "procedures": ["IV"],
    }
    response = client.post("/api/epcr/patients", json=payload, headers=headers)
    assert response.status_code == 201
    patient_id = response.json()["id"]

    response = client.get(f"/api/epcr/patients/{patient_id}")
    assert response.status_code == 200
