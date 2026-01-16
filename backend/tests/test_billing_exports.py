
def _register_user(client, email, org_name, role="dispatcher"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Billing User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="dispatcher"):
    headers, _ = _register_user(client, f"{role}@example.com", "BillingOrg", role=role)
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


def test_billing_edi_flow(client):
    headers = _auth_headers(client)
    claim_payload = {"invoice_number": "INV-9001", "payload": {"cpt": ["A0427"]}}
    response = client.post("/api/billing/claims/837p", json=claim_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "billing.claim.submitted")
    assert _has_audit(audits, "claim_submission")

    response = client.get("/api/billing/claims/837p", headers=headers)
    assert response.status_code == 200

    response = client.get("/api/billing/claims/INV-9001/hcfa-1500", headers=headers)
    assert response.status_code == 200

    rem_payload = {"payer": "Medicare", "claim_reference": "INV-9001"}
    response = client.post("/api/billing/remittance/835", json=rem_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "billing.remittance.imported")
    assert _has_audit(audits, "remittance_advice")

    ack_payload = {"ack_type": "999", "reference": "TA1-9001"}
    response = client.post("/api/billing/acks", json=ack_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "billing.ack.imported")
    assert _has_audit(audits, "clearinghouse_ack")

    elig_payload = {"patient_name": "Alex Stone", "payer": "Medicare"}
    response = client.post("/api/billing/eligibility/270", json=elig_payload, headers=headers)
    assert response.status_code == 201

    status_payload = {"claim_reference": "INV-9001"}
    response = client.post("/api/billing/claim-status/276", json=status_payload, headers=headers)
    assert response.status_code == 201

    statement_payload = {"patient_name": "Alex Stone", "balance_due": "$120"}
    response = client.post("/api/billing/statements", json=statement_payload, headers=headers)
    assert response.status_code == 201

    payment_payload = {"source": "Stripe", "amount": "$120"}
    response = client.post("/api/billing/payments", json=payment_payload, headers=headers)
    assert response.status_code == 201

    appeal_payload = {"claim_reference": "INV-9001"}
    response = client.post("/api/billing/appeals", json=appeal_payload, headers=headers)
    assert response.status_code == 201


def test_billing_cross_org_denied(client):
    headers_a, _ = _register_user(client, "bill_a@example.com", "BillingOrgA", role="dispatcher")
    response = client.post(
        "/api/billing/claims/837p",
        json={"invoice_number": "INV-9002", "payload": {"cpt": ["A0427"]}},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "bill_b@example.com", "BillingOrgB", role="dispatcher")
    response = client.get("/api/billing/claims/837p", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_billing_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/billing/claims/837p",
        json={"invoice_number": "INV-9003", "payload": {"cpt": ["A0427"]}},
        headers=headers,
    )
    assert response.status_code == 403
