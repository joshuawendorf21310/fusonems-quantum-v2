# Quantum Documents Audit Report

Date: 2026-01-16

## Route Inventory (/api/documents/*)
- Folders
  - `GET /api/documents/folders`
  - `POST /api/documents/folders`
  - `PATCH /api/documents/folders/{id}`
- Files
  - `GET /api/documents/files`
  - `POST /api/documents/files` (multipart upload)
  - `GET /api/documents/files/{id}` (metadata)
  - `GET /api/documents/files/{id}/download` (signed + auth)
  - `POST /api/documents/files/{id}/finalize`
  - `POST /api/documents/files/{id}/move`
  - `POST /api/documents/files/{id}/tag`
  - `DELETE /api/documents/files/{id}` (soft delete)
- Discovery Exports
  - `POST /api/documents/exports/discovery`
  - `GET /api/documents/exports/history`
  - `GET /api/documents/exports/{export_id}/download`

Source: `backend/services/documents/quantum_documents_router.py`

## Storage Backend Verification
- Local storage backend: `backend/utils/storage.py` (LocalStorageBackend)
- S3-compatible backend (DigitalOcean Spaces): `backend/utils/storage.py` (S3StorageBackend)
- Org-scoped prefixes: `build_storage_key(org_id, filename)` ensures `org_{org_id}/...`
- SHA-256 hashing on upload: `backend/services/documents/quantum_documents_router.py` (upload path)

## Retention Enforcement Summary
- Retention policy model: `backend/models/quantum_documents.py` (RetentionPolicy)
- Seeded defaults on org creation: `backend/utils/retention.py`, `backend/services/auth/auth_router.py`
- Deletion blocked during active retention: `backend/services/documents/quantum_documents_router.py`

## Legal Hold Enforcement Summary
- Legal holds stored in `backend/models/legal.py` and enforced by `utils/legal.py`
- Deletes blocked when hold exists; blocked attempts emit audit + event:
  - Audit: `utils/write_ops.py` → `utils/audit.py`
  - Event: `utils/events.py`
  - Block logging: `backend/services/documents/quantum_documents_router.py`

## Discovery Export Capability
- Export job record: `backend/models/quantum_documents.py` (DiscoveryExport)
- Artifact generated as ZIP with manifest: `backend/services/documents/quantum_documents_router.py`
- Stored in object storage backend with sha256: `backend/utils/storage.py`

## Test Evidence
Executed:
```
PYTHONPATH=. python3 -m pytest -q backend/tests/test_quantum_documents.py
```
Result: 5 passed

Tests implemented in: `backend/tests/test_quantum_documents.py`

## Requirement Status
- Upload (multipart): PASS
- List (folders + files): PASS
- Metadata fetch: PASS
- Signed download: PASS (signed URL + auth enforcement)
- Finalize (immutability): PASS (finalize endpoint + legal hold enforcement)
- Soft delete + enforcement: PASS
- Retention enforcement: PASS
- Legal hold enforcement + audit + event on blocked delete: PASS
- Storage abstraction (local + s3): PASS
- Discovery export scaffold: PASS
- Tests for org isolation / retention / legal hold / download auth / export artifact: PASS

## Known Limitations
- Signed download requires authenticated session; public pre-signed download tokens are not exposed for unauthenticated access. This is intentional for PHI safety.
