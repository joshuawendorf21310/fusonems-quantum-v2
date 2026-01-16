
def _register_user(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Batch Two User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="admin"):
    headers, _ = _register_user(client, f"{role}@example.com", "BatchTwoOrg", role=role)
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


def test_qa_case_flow(client):
    headers = _auth_headers(client, role="medical_director")
    rubric_payload = {"name": "Clinical Rubric", "criteria": [{"label": "Airway", "max": 10}]}
    response = client.post("/api/qa/rubrics", json=rubric_payload, headers=headers)
    assert response.status_code == 201
    rubric_id = response.json()["id"]

    case_payload = {"case_type": "clinical", "trigger": "cardiac arrest"}
    response = client.post("/api/qa/cases", json=case_payload, headers=headers)
    assert response.status_code == 201
    case_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "qa.case.created")
    assert _has_audit(audits, "qa_case")

    review_payload = {"case_id": case_id, "rubric_id": rubric_id, "scores": {"airway": 9}}
    response = client.post("/api/qa/reviews", json=review_payload, headers=headers)
    assert response.status_code == 201

    remediation_payload = {"case_id": case_id, "plan": "Airway refresher"}
    response = client.post("/api/qa/remediations", json=remediation_payload, headers=headers)
    assert response.status_code == 201


def test_qa_cross_org_denied(client):
    headers_a, _ = _register_user(client, "qa_a@example.com", "QAOrgA", role="medical_director")
    response = client.post(
        "/api/qa/cases", json={"case_type": "clinical", "trigger": "stroke"}, headers=headers_a
    )
    assert response.status_code == 201
    case_id = response.json()["id"]

    headers_b, _ = _register_user(client, "qa_b@example.com", "QAOrgB", role="medical_director")
    response = client.post(
        "/api/qa/reviews",
        json={"case_id": case_id, "scores": {"airway": 10}},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_qa_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    response = client.post("/api/qa/cases", json={"case_type": "clinical"}, headers=headers)
    assert response.status_code == 403


def test_comms_threads_messages(client):
    headers = _auth_headers(client, role="dispatcher")
    thread_payload = {"channel": "sms", "subject": "Unit update", "participants": ["Unit 3"]}
    response = client.post("/api/comms/threads", json=thread_payload, headers=headers)
    assert response.status_code == 201
    thread_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "comms.thread.created")
    assert _has_audit(audits, "comms_thread")

    message_payload = {"thread_id": thread_id, "sender": "Dispatch", "body": "Proceed to LZ"}
    response = client.post("/api/comms/messages", json=message_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "comms.message.created")
    assert _has_audit(audits, "comms_message")

    response = client.get(f"/api/comms/threads/{thread_id}/messages", headers=headers)
    assert response.status_code == 200


def test_comms_cross_org_denied(client):
    headers_a, _ = _register_user(client, "comms_a@example.com", "CommsOrgA", role="dispatcher")
    response = client.post(
        "/api/comms/threads",
        json={"channel": "sms", "subject": "OrgA Thread", "participants": ["Unit 1"]},
        headers=headers_a,
    )
    assert response.status_code == 201
    thread_id = response.json()["id"]

    headers_b, _ = _register_user(client, "comms_b@example.com", "CommsOrgB", role="dispatcher")
    response = client.post(
        "/api/comms/messages",
        json={"thread_id": thread_id, "sender": "OrgB", "body": "Cross org"},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_comms_rbac_denied(client):
    headers = _auth_headers(client, role="billing")
    response = client.post(
        "/api/comms/threads",
        json={"channel": "sms", "subject": "No Access", "participants": ["Unit 9"]},
        headers=headers,
    )
    assert response.status_code == 403


def test_training_center_records(client):
    headers = _auth_headers(client, role="founder")
    course_payload = {"title": "Cardiac Arrest Review", "credit_hours": 2}
    response = client.post("/api/training-center/courses", json=course_payload, headers=headers)
    assert response.status_code == 201
    course_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "training.course.created")
    assert _has_audit(audits, "training_course")

    enroll_payload = {"course_id": course_id, "user_id": 1}
    response = client.post("/api/training-center/enrollments", json=enroll_payload, headers=headers)
    assert response.status_code == 201

    credential_payload = {"user_id": 1, "credential_type": "ACLS", "issuer": "AHA"}
    response = client.post("/api/training-center/credentials", json=credential_payload, headers=headers)
    assert response.status_code == 201

    skill_payload = {"user_id": 1, "skill_name": "RSI", "evaluator": "Instructor"}
    response = client.post("/api/training-center/skills", json=skill_payload, headers=headers)
    assert response.status_code == 201

    ce_payload = {"user_id": 1, "category": "state", "hours": 4}
    response = client.post("/api/training-center/ce", json=ce_payload, headers=headers)
    assert response.status_code == 201


def test_training_center_cross_org_denied(client):
    headers_a, user_a_id = _register_user(client, "train_a@example.com", "TrainOrgA", role="admin")
    response = client.post(
        "/api/training-center/courses",
        json={"title": "OrgA Course", "credit_hours": 1},
        headers=headers_a,
    )
    assert response.status_code == 201
    course_id = response.json()["id"]

    headers_b, user_b_id = _register_user(client, "train_b@example.com", "TrainOrgB", role="admin")
    response = client.post(
        "/api/training-center/enrollments",
        json={"course_id": course_id, "user_id": user_b_id},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_training_center_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/training-center/courses",
        json={"title": "Unauthorized Course", "credit_hours": 1},
        headers=headers,
    )
    assert response.status_code == 403
