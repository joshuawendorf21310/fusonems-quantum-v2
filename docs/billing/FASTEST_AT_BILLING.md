# Fastest at Billing

**Product mandate:** FusionEMS Quantum v2 will be **the fastest at billing.** This doc defines what “fastest” means, how we achieve it, and what we measure.

---

## 1. What “Fastest at Billing” Means

- **Shortest time from transport complete to claim submitted** (and to payer/clearinghouse where applicable).
- **Fewest manual steps** — automation and one platform (ePCR + CAD + billing) so we don’t re-key or export/import.
- **First-pass acceptance** — validation and denial prevention upfront so speed doesn’t mean more denials.
- **We measure and optimize** — transport → claim created, claim created → submitted, submission → first response. We own these metrics and improve them.
- **Sole biller** — You’re the only biller. Automation, AI assist, and call/fax for missing facesheets are designed so one person can run billing without a team. See [Solo Biller Setup](../SOLO_BILLER_SETUP.md).

---

## 2. Speed Criteria (What We Optimize)

| Metric | Definition | Target (direction) |
|--------|------------|--------------------|
| **Transport → billing record** | Time from transport-complete event to billing record created | Minutes (automated; aim for &lt; 5 min) |
| **Billing record → claim ready** | Time to claim created with demographics, codes, medical necessity | Minutes (auto from ePCR + Metriport; minimal clicks) |
| **Claim ready → submitted** | Time from claim ready to submitted to Office Ally / payer | Minutes (batch submission; same-day) |
| **Submission → first response** | Clearinghouse/payer acknowledgment or first ERA | Track SLA; optimize submission quality |
| **First-pass acceptance rate** | % of submitted claims accepted without denial | Maximize (validation + assist upfront) |

---

## 3. How We Achieve It

### Automation

- **Transport complete → billing record:** CAD bridge / socket notifies billing; `handle_transport_completed` creates `BillingRecord` automatically. No manual “create billing” step.
- **ePCR + Metriport:** Patient demographics and insurance from Metriport; clinical data from ePCR. One source of truth; no re-keying.
- **Medical necessity / denial risk:** Billing assist runs before submission; denial-risk flags and medical-necessity snapshot stored on claim. Fix before submit, not after.
- **Batch submission:** Office Ally (and 837P) batch so multiple claims go out in one action; founder/billing can trigger batch and see status.

### Fewer Steps

- **One platform:** ePCR, CAD, and billing in one system. No export from ePCR → import to billing.
- **Claim creation from ePCR/patient:** Create claim from `epcr_patient_id`; demographics and assist snapshot pulled automatically.
- **Validation upfront:** Required fields and NEMSIS/billing rules validated before claim is “ready”; UI blocks or warns so we don’t submit invalid claims.

### Denial Prevention (So “Fast” ≠ “Fast to Denial”)

- **Ready check:** `GET /api/billing/claims/ready_check?epcr_patient_id=...` (and equivalent UI) so billing sees what’s missing before creating/submitting.
- **Assist snapshot:** Medical necessity hints and denial-risk flags on claim; address issues before submission.
- **Training mode:** Test claims without affecting production submission; validate flow and data without sending to payer.

### Missing Facesheet: AI Call or Fax

- When facesheet (demographics from facility) is missing, we don’t block on manual follow-up only. **AI can call** the hospital (AI-assisted request; optional outbound call to facility) or we **get it via fax** (inbound fax parsed and matched automatically; optional outbound fax request to facility when we have fax number). See [Facesheet: Call or Fax](FACESHEET_CALL_OR_FAX.md).

---

## 4. Current Implementation Hooks

- **Transport complete → billing:** `backend/services/cad/bridge_handlers.py` — `handle_transport_completed()` creates `BillingRecord`, triggers billing workflow.
- **Crew notifies transport complete:** `backend/services/cad/socket_router.py` — `POST /transport/completed` (crew role).
- **Claim creation:** `backend/services/billing/claims_router.py` — `POST /api/billing/claims` with `epcr_patient_id`; demographics and assist snapshot from patient + assist result.
- **Office Ally batch:** `backend/services/billing/office_ally_sync.py` — `OfficeAllyClient.sync_claims()` builds EDI, uploads, marks claims submitted.
- **837P submission:** `backend/services/billing/billing_router.py` — `POST /claims/837p` for claim submission payload.

Gaps to close for “fastest”:

- **Metrics:** Instrument and store timestamps (transport_completed_at, billing_record_created_at, claim_created_at, claim_submitted_at) and expose in founder/billing analytics.
- **Auto-claim creation (optional):** After billing record is created, optionally auto-create claim when ePCR is finalized and ready-check passes (configurable per org).
- **Dashboard:** Billing speed dashboard: transport → claim → submitted (avg/min/max), first-pass rate, pending count.

---

## 5. References

- [Product Mandate](../PRODUCT_MANDATE.md) — “Fastest at Billing” section.
- [Facesheet: Call or Fax](FACESHEET_CALL_OR_FAX.md) — AI call or fax when facesheet is missing.
- [Stripe + Office Ally Flow](stripe-office-ally-flow.md) — Insurance vs patient responsibility flow.
- [Solo Biller Setup](../SOLO_BILLER_SETUP.md) — Billing setup and configuration.

---

*Last updated: January 2026.*
