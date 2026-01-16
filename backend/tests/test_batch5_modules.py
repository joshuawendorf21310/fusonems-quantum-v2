
def _register_user(client, email, org_name, role="provider"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Batch Five User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="provider"):
    headers, _ = _register_user(client, f"{role}@example.com", "BatchFiveOrg", role=role)
    return headers


def _list_events(client, headers):
    response = client.get("/api/events", headers=headers)
    assert response.status_code == 200
    return response.json()


def _list_audits(client, headers):
    response = client.get("/api/compliance/forensic", headers=headers)
    assert response.status_code == 200
    return response.json()


def _has_event(events, event_type):
    return any(event.get("event_type") == event_type for event in events)


def _has_audit(audits, resource, action="create"):
    return any(
        audit.get("resource") == resource and audit.get("action") == action for audit in audits
    )


def test_narcotics_flow(client):
    headers = _auth_headers(client)
    payload = {"name": "Fentanyl", "quantity": "5", "storage_location": "NarcBox"}
    response = client.post("/api/narcotics/items", json=payload, headers=headers)
    assert response.status_code == 201
    narcotic_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "narcotics.item.created")
    assert _has_audit(audits, "narcotic_item")

    custody_payload = {"narcotic_id": narcotic_id, "event_type": "transfer", "quantity": "5"}
    response = client.post("/api/narcotics/custody", json=custody_payload, headers=headers)
    assert response.status_code == 201

    discrepancy_payload = {"narcotic_id": narcotic_id, "summary": "Count mismatch"}
    response = client.post("/api/narcotics/discrepancies", json=discrepancy_payload, headers=headers)
    assert response.status_code == 201


def test_narcotics_cross_org_denied(client):
    headers_a, _ = _register_user(client, "narc_a@example.com", "NarcOrgA", role="provider")
    response = client.post(
        "/api/narcotics/items",
        json={"name": "Morphine", "quantity": "3", "storage_location": "Safe"},
        headers=headers_a,
    )
    assert response.status_code == 201
    narcotic_id = response.json()["id"]

    headers_b, _ = _register_user(client, "narc_b@example.com", "NarcOrgB", role="provider")
    response = client.post(
        "/api/narcotics/custody",
        json={"narcotic_id": narcotic_id, "event_type": "transfer", "quantity": "3"},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_narcotics_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post(
        "/api/narcotics/items",
        json={"name": "Ketamine", "quantity": "1", "storage_location": "Locker"},
        headers=headers,
    )
    assert response.status_code == 403


def test_medication_flow(client):
    headers = _auth_headers(client)
    payload = {"name": "Aspirin", "routes": ["PO"]}
    response = client.post("/api/medication/master", json=payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "medication.master.created")
    assert _has_audit(audits, "medication_master")

    admin_payload = {"medication_name": "Aspirin", "dose": "325", "dose_units": "mg"}
    response = client.post("/api/medication/administrations", json=admin_payload, headers=headers)
    assert response.status_code == 201


def test_medication_cross_org_denied(client):
    headers_a, _ = _register_user(client, "med_a@example.com", "MedOrgA", role="provider")
    response = client.post(
        "/api/medication/master",
        json={"name": "Ibuprofen", "routes": ["PO"]},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "med_b@example.com", "MedOrgB", role="provider")
    response = client.get("/api/medication/master", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_medication_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post(
        "/api/medication/master",
        json={"name": "Lidocaine", "routes": ["IV"]},
        headers=headers,
    )
    assert response.status_code == 403


def test_inventory_flow(client):
    headers = _auth_headers(client)
    payload = {"name": "Airway Kit", "quantity_on_hand": 2, "location": "Station 1"}
    response = client.post("/api/inventory/items", json=payload, headers=headers)
    assert response.status_code == 201
    item_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "inventory.item.created")
    assert _has_audit(audits, "inventory_item")

    move_payload = {"item_id": item_id, "movement_type": "transfer", "quantity": 1}
    response = client.post("/api/inventory/movements", json=move_payload, headers=headers)
    assert response.status_code == 201

    rig_payload = {"unit_id": "A-14", "status": "pass"}
    response = client.post("/api/inventory/rig-checks", json=rig_payload, headers=headers)
    assert response.status_code == 201


def test_inventory_cross_org_denied(client):
    headers_a, _ = _register_user(client, "inv_a@example.com", "InvOrgA", role="provider")
    response = client.post(
        "/api/inventory/items",
        json={"name": "O2 Tank", "quantity_on_hand": 1, "location": "Station 2"},
        headers=headers_a,
    )
    assert response.status_code == 201
    item_id = response.json()["id"]

    headers_b, _ = _register_user(client, "inv_b@example.com", "InvOrgB", role="provider")
    response = client.post(
        "/api/inventory/movements",
        json={"item_id": item_id, "movement_type": "transfer", "quantity": 1},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_inventory_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post(
        "/api/inventory/items",
        json={"name": "Splint", "quantity_on_hand": 1, "location": "Rig"},
        headers=headers,
    )
    assert response.status_code == 403


def test_fleet_flow(client):
    headers = _auth_headers(client, role="dispatcher")
    payload = {"vehicle_id": "AMB-14", "call_sign": "A-14"}
    response = client.post("/api/fleet/vehicles", json=payload, headers=headers)
    assert response.status_code == 201
    vehicle_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "fleet.vehicle.created")
    assert _has_audit(audits, "fleet_vehicle")

    maint_payload = {"vehicle_id": vehicle_id, "service_type": "oil_change"}
    response = client.post("/api/fleet/maintenance", json=maint_payload, headers=headers)
    assert response.status_code == 201

    insp_payload = {"vehicle_id": vehicle_id, "status": "pass"}
    response = client.post("/api/fleet/inspections", json=insp_payload, headers=headers)
    assert response.status_code == 201

    telemetry_payload = {"vehicle_id": vehicle_id, "latitude": "43.0", "longitude": "-87.9"}
    response = client.post("/api/fleet/telemetry", json=telemetry_payload, headers=headers)
    assert response.status_code == 201


def test_fleet_cross_org_denied(client):
    headers_a, _ = _register_user(client, "fleet_a@example.com", "FleetOrgA", role="dispatcher")
    response = client.post(
        "/api/fleet/vehicles",
        json={"vehicle_id": "MED-1", "call_sign": "M-1"},
        headers=headers_a,
    )
    assert response.status_code == 201
    vehicle_id = response.json()["id"]

    headers_b, _ = _register_user(client, "fleet_b@example.com", "FleetOrgB", role="dispatcher")
    response = client.post(
        "/api/fleet/maintenance",
        json={"vehicle_id": vehicle_id, "service_type": "tires"},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_fleet_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/fleet/vehicles",
        json={"vehicle_id": "MED-2", "call_sign": "M-2"},
        headers=headers,
    )
    assert response.status_code == 403
