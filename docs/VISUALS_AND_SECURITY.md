# Visuals & Security — Complete All Checklist

**Goal:** Complete all **enhancements**, **visuals**, and **security** so we beat all vendors and ship production-grade from day one. Every item aligns with the [Product Mandate](PRODUCT_MANDATE.md).

---

## 1. Visuals (UI/UX)

### Design system

- [x] **Design tokens** — `globals.css`: charcoal, orange, red; FusionCare (cyan), TransportLink (emerald); accent, success, warning, error.
- [ ] **No placeholder copy** — Audit all shipped pages; replace “Lorem”, “TODO”, generic labels with real workflows and labels.
- [ ] **Agency/role-specific** — Fire vs EMS vs HEMS vs billing: each flow uses role-appropriate language and actions.

### Dashboards

- [x] **Billing dashboard** — Cards (Pending, Ready, Submitted, Denied, Paid MTD); sole biller callout; FacesheetStatus, OfficeAllyTracker, AIAssistPanel.
- [x] **Billing speed section** — Avg claim→submitted (hours), first-pass rate, submitted MTD, pending (from `/api/billing/console/speed`).
- [x] **Founder dashboards** — "So what?" quick-link panel (Billing dashboard, BAA status, Claims, Terminology, ePCR) on Founder page.
- [x] **Compliance/BAA** — Vendor table with status (Obtain/Signed), renewal; link to Founder Compliance; `/compliance/baa`.

### Accessibility & responsive

- [ ] **Focus and contrast** — Key flows (login, billing submit, ePCR save) meet contrast and focus order.
- [ ] **Labels** — All form inputs have visible or aria labels.
- [ ] **Mobile/tablet** — Billing, ePCR, MDT responsive; PWAs usable on device.

---

## 2. Security (production-grade from day one)

### Auth & rate limiting

- [x] **JWT + roles + MFA** — core/auth; require_roles, require_mfa where required.
- [x] **Rate limiting** — AUTH_RATE_LIMIT_PER_MIN in config; apply to auth endpoints.

### Secrets & config

- [x] **No hardcoded secrets** — All keys in env; .env.example documented; PRODUCTION_STATUS redacted.
- [x] **Encryption at rest** — STORAGE_ENCRYPTION_KEY and DOCS_ENCRYPTION_KEY in config; document storage and PHI fields use encryption at rest when backend storage (e.g. S3/Spaces) has server-side encryption enabled. Sensitive columns (e.g. tokens) should use application-level encryption where required.

### BAA & compliance

- [x] **BAA doc** — [BAA_AND_BREACH](compliance/BAA_AND_BREACH.md): vendor list, breach workflow, OCR link.
- [x] **BAA page** — `/compliance/baa`: vendor list + status table; link to Founder Compliance.
- [ ] **BAA dashboard** — Founder: list vendors, BAA status, renewal date (optional widget).

### Audit & events

- [x] **Audit events** — audit_event, ForensicAuditLog; event_type for billing, auth, PHI access.
- [ ] **Audit UI** — Founder/Compliance: view recent audit log (filter by resource, user, date).

### Backup / DR / monitoring

- [x] **Backup/DR doc** — [BACKUP_DR_MONITORING](operations/BACKUP_DR_MONITORING.md).
- [x] **Health checks** — `/health` and `/healthz`; used by load balancer and monitoring.

### Webhooks & CSRF

- [x] **Telnyx signature** — verify_telnyx_signature on webhooks.
- [x] **Stripe webhook** — Verify Stripe signature on billing webhooks.
- [ ] **CSRF** — Cookie + header for state-changing requests (if not already applied).

---

## 3. Enhancements (from Beat All Vendors roadmap)

- **Billing:** Speed metrics API + dashboard (done); auto-claim optional; outbound call/fax facesheet.
- **ePCR/NEMSIS:** Full NEMSIS XML; state submission; terminology builder; AI suggests.
- **Visuals:** No placeholder; BAA vendor table; “so what?” actions on dashboards.
- **Security:** BAA dashboard (optional); audit UI; encryption documented; health check.

---

## 4. References

- [Product Mandate](PRODUCT_MANDATE.md) — Ship checklist, principles.
- [Beat All Vendors Roadmap](BEAT_ALL_VENDORS_ROADMAP.md) — §10 Visuals, §11 Security, §12 Complete All.
- [BAA & Breach](compliance/BAA_AND_BREACH.md) — BAA tracking, breach workflow.
- [Backup / DR / Monitoring](operations/BACKUP_DR_MONITORING.md) — Operations runbook.
- [Encryption at Rest](operations/ENCRYPTION.md) — Config keys and usage.

---

*Last updated: January 2026.*
