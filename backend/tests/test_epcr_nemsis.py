
def _auth_headers(client, role="provider"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{role}@example.com",
            "full_name": "ePCR User",
            "password": "securepass",
            "role": role,
            "organization_name": "EpcrOrg",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_nemsis_validation_and_exports(client):
    headers = _auth_headers(client)
    payload = {
        "first_name": "Alex",
        "last_name": "Stone",
        "date_of_birth": "1990-01-01",
        "incident_number": "INC-9001",
        "vitals": {"hr": 88, "bp_systolic": 118},
    }
    response = client.post("/api/epcr/patients", json=payload, headers=headers)
    assert response.status_code == 201
    patient_id = response.json()["id"]

    response = client.get(f"/api/epcr/patients/{patient_id}/nemsis/validate", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] in {"PASS", "FAIL"}

    response = client.get(f"/api/epcr/patients/{patient_id}/exports/nemsis", headers=headers)
    assert response.status_code == 200
    assert response.json()["export"]["incident_number"] == "INC-9001"


def test_epcr_ocr_and_labs(client):
    headers = _auth_headers(client)
    payload = {
        "first_name": "Morgan",
        "last_name": "Riley",
        "date_of_birth": "1984-02-10",
        "incident_number": "INC-9002",
    }
    response = client.post("/api/epcr/patients", json=payload, headers=headers)
    assert response.status_code == 201
    patient_id = response.json()["id"]

    ocr_payload = {
        "device_type": "monitor",
        "device_name": "ZOLL X",
        "fields": {"heart_rate": 102, "spo2": 94},
        "confidence": 0.93,
    }
    response = client.post(f"/api/epcr/patients/{patient_id}/ocr", json=ocr_payload, headers=headers)
    assert response.status_code == 201

    lab_payload = {"lab_type": "CBC", "values": {"wbc": "12.1"}}
    response = client.post(f"/api/epcr/patients/{patient_id}/labs", json=lab_payload, headers=headers)
    assert response.status_code == 201

    narrative_payload = {"narrative": "Stable transport with vitals monitored."}
    response = client.post(
        f"/api/epcr/patients/{patient_id}/narrative", json=narrative_payload, headers=headers
    )
    assert response.status_code == 200
