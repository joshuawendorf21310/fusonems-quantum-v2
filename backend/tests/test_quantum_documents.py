import io
from pathlib import Path

from core.config import settings
from core.database import SessionLocal
from models.compliance import ForensicAuditLog
from models.event import EventLog
from models.organization import Organization
from models.quantum_documents import DiscoveryExport, RetentionPolicy


def _register(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Docs User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload_file(client, headers, retention_policy_id=None):
    file_payload = io.BytesIO(b"quantum-docs")
    data = {
        "classification": "ops",
        "tags": '["vault"]',
    }
    if retention_policy_id is not None:
        data["retention_policy_id"] = str(retention_policy_id)
    response = client.post(
        "/api/documents/files",
        headers=headers,
        data=data,
        files={"file": ("run-sheet.txt", file_payload, "text/plain")},
    )
    assert response.status_code == 201
    return response.json()


def test_docs_org_isolation(client, tmp_path):
    settings.DOCS_STORAGE_LOCAL_DIR = str(tmp_path)
    org_a = _register(client, "docs-a@example.com", "DocsOrgA")
    org_b = _register(client, "docs-b@example.com", "DocsOrgB")

    _upload_file(client, org_a)

    response = client.get("/api/documents/files", headers=org_b)
    assert response.status_code == 200
    assert response.json() == []


def test_docs_retention_blocks_delete(client, tmp_path):
    original = settings.SMART_MODE
    settings.SMART_MODE = False
    settings.DOCS_STORAGE_LOCAL_DIR = str(tmp_path)
    headers = _register(client, "retain@example.com", "RetentionOrg")

    session = SessionLocal()
    org = session.query(Organization).filter(Organization.name == "RetentionOrg").first()
    policy = RetentionPolicy(
        org_id=org.id,
        name="Retention Test",
        applies_to="ops",
        retention_days=365,
        delete_behavior="soft_delete",
        legal_hold_behavior="always_freeze",
    )
    session.add(policy)
    session.commit()
    session.refresh(policy)
    session.close()

    doc = _upload_file(client, headers, retention_policy_id=policy.id)
    response = client.delete(f"/api/documents/files/{doc['id']}", headers=headers)
    settings.SMART_MODE = original
    assert response.status_code == 423
    payload = response.json()
    assert payload["decision"] == "BLOCK"
    assert "DOC.RETENTION.BLOCK_DELETE.v1" in payload["rule_ids"]


def test_docs_legal_hold_blocks_delete_and_audits(client, tmp_path):
    original = settings.SMART_MODE
    settings.SMART_MODE = False
    settings.DOCS_STORAGE_LOCAL_DIR = str(tmp_path)
    headers = _register(client, "hold@example.com", "HoldOrg")

    doc = _upload_file(client, headers)
    hold_payload = {"scope_type": "document_file", "scope_id": doc["id"], "reason": "legal"}
    response = client.post("/api/legal-hold", json=hold_payload, headers=headers)
    assert response.status_code == 201

    response = client.delete(f"/api/documents/files/{doc['id']}", headers=headers)
    settings.SMART_MODE = original
    assert response.status_code == 423
    payload = response.json()
    assert payload["decision"] == "BLOCK"
    assert "DOC.LEGAL_HOLD.BLOCK_DELETE.v1" in payload["rule_ids"]

    session = SessionLocal()
    audit = (
        session.query(ForensicAuditLog)
        .filter(ForensicAuditLog.resource == "documents_file", ForensicAuditLog.decision_id != "")
        .first()
    )
    event = (
        session.query(EventLog)
        .filter(EventLog.event_type == "documents.file.delete_blocked")
        .first()
    )
    session.close()
    assert audit is not None
    assert event is not None


def test_docs_download_requires_auth(client, tmp_path):
    settings.DOCS_STORAGE_LOCAL_DIR = str(tmp_path)
    headers = _register(client, "download@example.com", "DownloadOrg")
    doc = _upload_file(client, headers)

    client.cookies.clear()
    response = client.get(f"/api/documents/files/{doc['id']}/download")
    assert response.status_code in {401, 403}


def test_docs_discovery_export_creates_artifact(client, tmp_path):
    settings.DOCS_STORAGE_LOCAL_DIR = str(tmp_path)
    headers = _register(client, "export@example.com", "ExportOrg")
    _upload_file(client, headers)

    response = client.post("/api/documents/exports/discovery", headers=headers, data={})
    assert response.status_code == 201
    export_id = response.json()["export_id"]

    session = SessionLocal()
    export = session.query(DiscoveryExport).filter(DiscoveryExport.id == export_id).first()
    assert export is not None
    assert export.status == "complete"
    assert export.storage_key
    session.close()

    artifact_path = Path(tmp_path) / export.storage_key
    assert artifact_path.exists()
