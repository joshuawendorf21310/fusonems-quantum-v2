
def _register_user(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Foundation User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]["id"]


def _auth_headers(client, role="admin"):
    headers, _ = _register_user(client, f"{role}@example.com", "FoundationOrg", role=role)
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


def test_document_studio_templates_and_records(client):
    headers = _auth_headers(client, role="admin")
    template_payload = {
        "name": "QA Summary",
        "module_key": "COMPLIANCE",
        "sections": [{"title": "Summary", "fields": ["score", "reviewer"]}],
    }
    response = client.post("/api/documents/templates", json=template_payload, headers=headers)
    assert response.status_code == 201
    template_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "document_studio.template.created")
    assert _has_audit(audits, "document_template")

    response = client.post(
        f"/api/documents/templates/{template_id}/activate",
        json={"status": "active"},
        headers=headers,
    )
    assert response.status_code == 200

    record_payload = {
        "template_id": template_id,
        "title": "QA-001",
        "output_format": "PDF",
        "content": {"score": 98},
        "classification": "PHI",
    }
    response = client.post("/api/documents/records", json=record_payload, headers=headers)
    assert response.status_code == 201
    record_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "document_studio.record.created")
    assert _has_audit(audits, "document_record")

    response = client.post(f"/api/documents/records/{record_id}/finalize", headers=headers)
    assert response.status_code == 200


def test_document_studio_cross_org_denied(client):
    headers_a, _ = _register_user(client, "docs_a@example.com", "DocsOrgA", role="admin")
    template_payload = {
        "name": "Cross Org Template",
        "module_key": "COMPLIANCE",
        "sections": [{"title": "Summary", "fields": ["score"]}],
    }
    response = client.post("/api/documents/templates", json=template_payload, headers=headers_a)
    assert response.status_code == 201
    template_id = response.json()["id"]

    headers_b, _ = _register_user(client, "docs_b@example.com", "DocsOrgB", role="admin")
    record_payload = {
        "template_id": template_id,
        "title": "Cross Org Record",
        "output_format": "PDF",
        "content": {"score": 88},
        "classification": "PHI",
    }
    response = client.post("/api/documents/records", json=record_payload, headers=headers_b)
    assert response.status_code == 403


def test_document_studio_rbac_denied(client):
    headers = _auth_headers(client, role="dispatcher")
    template_payload = {
        "name": "Denied Template",
        "module_key": "COMPLIANCE",
        "sections": [{"title": "Summary", "fields": ["score"]}],
    }
    response = client.post("/api/documents/templates", json=template_payload, headers=headers)
    assert response.status_code == 403


def test_builder_registry_flow(client):
    headers = _auth_headers(client, role="founder")
    payload = {
        "builder_key": "validation_rules",
        "version": "v1",
        "status": "active",
        "description": "Base rule set",
        "impacted_modules": ["EPCR"],
    }
    response = client.post("/api/builders/registry", json=payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "builders.registry.created")
    assert _has_audit(audits, "builder_registry")

    update_payload = {
        "version": "v2",
        "change_summary": "Added trauma block",
    }
    response = client.patch("/api/builders/registry/validation_rules", json=update_payload, headers=headers)
    assert response.status_code == 200
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "builders.registry.updated")
    assert _has_audit(audits, "builder_registry", action="update")

    response = client.get("/api/builders/logs", headers=headers)
    assert response.status_code == 200


def test_builders_cross_org_denied(client):
    headers_a, _ = _register_user(client, "build_a@example.com", "BuildOrgA", role="founder")
    payload = {
        "builder_key": "dispatch_rules",
        "version": "v1",
        "status": "active",
        "description": "Dispatch rules",
        "impacted_modules": ["CAD"],
    }
    response = client.post("/api/builders/registry", json=payload, headers=headers_a)
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "build_b@example.com", "BuildOrgB", role="founder")
    response = client.get("/api/builders/registry", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_builders_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    payload = {
        "builder_key": "policy_rules",
        "version": "v1",
        "status": "active",
        "description": "Policy rules",
        "impacted_modules": ["EPCR"],
    }
    response = client.post("/api/builders/registry", json=payload, headers=headers)
    assert response.status_code == 403


def test_search_index_and_saved_queries(client):
    headers = _auth_headers(client, role="admin")
    index_payload = {
        "module_key": "HEMS",
        "record_id": "mission-99",
        "title": "Mission 99",
        "body": "Weather hold then lift",
        "tags": ["weather", "hold"],
    }
    response = client.post("/api/search/index", json=index_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "search.index.created")
    assert _has_audit(audits, "search_index", action="index")

    response = client.get("/api/search?query=weather", headers=headers)
    assert response.status_code == 200
    assert response.json()

    saved_payload = {"name": "Weather Holds", "query": "weather", "filters": {}}
    response = client.post("/api/search/saved", json=saved_payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "search.saved.created")
    assert _has_audit(audits, "saved_search")


def test_search_cross_org_denied(client):
    headers_a, _ = _register_user(client, "search_a@example.com", "SearchOrgA", role="admin")
    response = client.post(
        "/api/search/index",
        json={
            "module_key": "CAD",
            "record_id": "call-1",
            "title": "Call 1",
            "body": "Test call",
            "tags": ["test"],
        },
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "search_b@example.com", "SearchOrgB", role="admin")
    response = client.get("/api/search?query=call", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_search_rbac_denied(client):
    headers = _auth_headers(client, role="billing")
    response = client.post(
        "/api/search/index",
        json={
            "module_key": "CAD",
            "record_id": "call-2",
            "title": "Call 2",
            "body": "Test call",
        },
        headers=headers,
    )
    assert response.status_code == 403


def test_jobs_queue(client):
    headers = _auth_headers(client, role="founder")
    response = client.post("/api/jobs", json={"job_type": "export_bundle"}, headers=headers)
    assert response.status_code == 201
    job_id = response.json()["id"]
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "jobs.job.created")
    assert _has_audit(audits, "job_queue")

    response = client.post(f"/api/jobs/{job_id}/run", headers=headers)
    assert response.status_code == 200
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "jobs.job.run_started")
    assert _has_audit(audits, "job_queue", action="run")


def test_jobs_cross_org_denied(client):
    headers_a, _ = _register_user(client, "jobs_a@example.com", "JobsOrgA", role="founder")
    response = client.post("/api/jobs", json={"job_type": "ops_export"}, headers=headers_a)
    assert response.status_code == 201
    job_id = response.json()["id"]

    headers_b, _ = _register_user(client, "jobs_b@example.com", "JobsOrgB", role="founder")
    response = client.post(f"/api/jobs/{job_id}/run", headers=headers_b)
    assert response.status_code == 403


def test_jobs_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post("/api/jobs", json={"job_type": "ops_export"}, headers=headers)
    assert response.status_code == 403


def test_analytics_and_usage(client):
    headers = _auth_headers(client, role="founder")
    response = client.post(
        "/api/analytics/metrics",
        json={"metric_key": "api_uptime", "metric_value": "99.9%"},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "analytics.metric.created")
    assert _has_audit(audits, "analytics_metric")

    response = client.post(
        "/api/analytics/usage",
        json={"event_key": "builder_publish", "module_key": "BUILDERS"},
        headers=headers,
    )
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "analytics.usage.created")
    assert _has_audit(audits, "usage_event")


def test_analytics_cross_org_denied(client):
    headers_a, _ = _register_user(client, "ana_a@example.com", "AnalyticsOrgA", role="founder")
    response = client.post(
        "/api/analytics/metrics",
        json={"metric_key": "latency", "metric_value": "120ms"},
        headers=headers_a,
    )
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "ana_b@example.com", "AnalyticsOrgB", role="founder")
    response = client.get("/api/analytics/metrics", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_analytics_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    response = client.post(
        "/api/analytics/metrics",
        json={"metric_key": "latency", "metric_value": "120ms"},
        headers=headers,
    )
    assert response.status_code == 403


def test_feature_flags(client):
    headers = _auth_headers(client, role="founder")
    payload = {
        "flag_key": "pwa_force_upgrade",
        "module_key": "FEATURE_FLAGS",
        "enabled": True,
        "scope": "global",
    }
    response = client.post("/api/feature-flags", json=payload, headers=headers)
    assert response.status_code == 201
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "feature_flags.created")
    assert _has_audit(audits, "feature_flag")

    response = client.patch(
        "/api/feature-flags/pwa_force_upgrade",
        json={"enabled": False, "rules": {"mode": "soft"}},
        headers=headers,
    )
    assert response.status_code == 200
    events = _list_events(client, headers)
    audits = _list_audits(client, headers)
    assert _has_event(events, "feature_flags.updated")
    assert _has_audit(audits, "feature_flag", action="update")


def test_feature_flags_cross_org_denied(client):
    headers_a, _ = _register_user(client, "flags_a@example.com", "FlagsOrgA", role="founder")
    payload = {
        "flag_key": "flag_a",
        "module_key": "FEATURE_FLAGS",
        "enabled": True,
        "scope": "global",
    }
    response = client.post("/api/feature-flags", json=payload, headers=headers_a)
    assert response.status_code == 201

    headers_b, _ = _register_user(client, "flags_b@example.com", "FlagsOrgB", role="founder")
    response = client.get("/api/feature-flags", headers=headers_b)
    assert response.status_code == 200
    assert not response.json()


def test_feature_flags_rbac_denied(client):
    headers = _auth_headers(client, role="provider")
    payload = {
        "flag_key": "flag_b",
        "module_key": "FEATURE_FLAGS",
        "enabled": True,
        "scope": "global",
    }
    response = client.post("/api/feature-flags", json=payload, headers=headers)
    assert response.status_code == 403
