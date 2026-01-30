# Encryption at Rest — Configuration and Usage

**Goal:** Document how FusionEMS Quantum v2 uses encryption for sensitive data and storage so security and compliance (e.g. BAA, HIPAA) are clear.

---

## 1. Config Keys

| Key | Purpose |
|-----|--------|
| `STORAGE_ENCRYPTION_KEY` | Application-level encryption for stored blobs (e.g. documents, exports) when using object storage (S3/Spaces). Use a 32-byte key (e.g. from `openssl rand -base64 32`). |
| `DOCS_ENCRYPTION_KEY` | Encryption for PHI-bearing documents (facesheets, attachments). Same format as above. |

- **No hardcoded secrets:** Keys live in environment variables only; see `backend/.env.example`.
- **Rotation:** Rotate keys per org policy; re-encrypt existing data if required by your procedures.

---

## 2. Where Encryption Is Used

- **Object storage (S3/Spaces):** When server-side encryption (SSE) is enabled on the bucket, objects are encrypted at rest. Application keys above can be used for additional client-side encryption of sensitive blobs if implemented.
- **Database:** Sensitive columns (e.g. API tokens, webhook secrets) should use application-level encryption where required; config keys can drive that.
- **PHI documents:** Document storage service uses `DOCS_ENCRYPTION_KEY` for PHI-bearing files when client-side encryption is enabled.

---

## 3. TLS in Transit

- All API and frontend traffic should use HTTPS (TLS) in production.
- Webhook endpoints (Telnyx, Stripe) verify signatures; TLS is required for callbacks.

---

## 4. References

- [Visuals & Security](../VISUALS_AND_SECURITY.md) — Security checklist.
- [Beat All Vendors Roadmap](../BEAT_ALL_VENDORS_ROADMAP.md) — §11 Security.
- [Backup / DR / Monitoring](BACKUP_DR_MONITORING.md) — Operations runbook.

---

*Last updated: January 2026.*
