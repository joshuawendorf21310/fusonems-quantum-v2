# 100% Completion, Wisconsin Certification & Compliance

This document defines the **100% completion** scope for FusionEMS Quantum: CMS, NEMSIS, and NFIRS compliance; Wisconsin certification wiring; third-party billing import; agency data export; and terminology builders (ICD-10, SNOMED, RXNorm) that follow NEMSIS constraints.

---

## 1. Wisconsin-first wiring for certification

To become **Wisconsin certified**, the platform must:

| Requirement | Status | Implementation |
|-------------|--------|-----------------|
| NEMSIS 3.x export for ePCR | Partial | Payload on finalize; full XML + state submit to be completed. |
| Wisconsin state submission | Partial | Set `NEMSIS_STATE_CODES=WI` and `NEMSIS_STATE_ENDPOINTS` (Wisconsin EMS URL when provided). |
| Default state = WI | Done | ePCR record `nemsis_state` default "WI"; Wisconsin billing config `state="WI"`. |
| Wisconsin billing (tax, templates) | Done | `WisconsinBillingService`, `WisconsinBillingConfig`, patient statements for WI. |
| NFIRS export (fire) | Done | NFIRS export endpoint and NFIRS 5.0-aligned export service. |
| CMS-compliant billing | Partial | 837P/Office Ally; CMS CCN, HIPAA; full CMS audit trail to be verified. |

**Config for Wisconsin certification (in `.env`):**

- `NEMSIS_STATE_CODES=WI`
- `NEMSIS_STATE_ENDPOINTS={"WI": "https://<wisconsin-ems-submission-url>"}` (when Wisconsin provides the URL)
- Wisconsin billing: use Founder dashboard → Billing → Wisconsin to enable and configure.

---

## 2. Compliance: CMS, NEMSIS, NFIRS

### CMS compliance

- **Billing:** 837P generation, Office Ally sync, eligibility/remittance; HIPAA-safe handling of PHI.
- **Documentation:** Audit trail for billing actions; no forgery of signatures or dates.
- **Export:** Ability to produce CMS-acceptable claim data and supporting documentation for audits.

**100% target:** Full CMS audit trail, 837P validation, and export of all billing data for audits.

### NEMSIS compliance

- **ePCR:** NEMSIS 3.x data set alignment; required elements present and valid.
- **Schematron (3.5.1):** At ePCR finalize, the platform runs NEMSIS 3.5.1–aligned Schematron rules (DB-stored `EpcrSchematronRule` plus built-in required elements). Results are stored in `NEMSISValidationResult` with `validator_version` "rule-engine-1.0+schematron-3.5.1". Add custom rules via ePCR Builders → Schematron rules (version 3.5.1).
- **Export:** NEMSIS XML (or state-specified format) generated from ePCR on finalize; submission to state registry when configured.
- **Terminology:** Diagnosis (ICD-10), interventions (SNOMED where applicable), medications (RXNorm) constrained to NEMSIS-allowed or state-accepted values where required.

**100% target:** Full NEMSIS 3.x XML export, state submission wired, terminology builders NEMSIS-constrained.

**NEMSIS update watch:** The platform can check for NEMSIS standard updates and notify founders:
- **Founder:** `GET /api/founder/nemsis-watch/status` (last known version, last check time); `POST /api/founder/nemsis-watch/check` (fetch current version, compare, notify if newer).
- **Cron:** Call `POST /api/cron/nemsis-watch` with header `X-Cron-Secret: <NEMSIS_WATCH_CRON_SECRET>` (e.g. daily). Set `NEMSIS_WATCH_CRON_SECRET` and optionally `NEMSIS_VERSION_CHECK_URL` in `.env`. When a newer version is detected, founders receive an in-app notification and an email to `FOUNDER_EMAIL`.

### NFIRS compliance

- **Fire:** NFIRS 5.0-aligned structure; Basic, Fire, Structure modules; provenance (MDT-derived, no fabricated times).
- **Export:** NFIRS JSON/XML export per incident; batch export by date range.

**100% target:** NFIRS export complete and validated against NFIRS 5.0 spec; all required modules populated where data exists.

---

## 3. Terminology builders (NEMSIS-constrained)

You need **builders** so you can **add new codes** and keep them within NEMSIS constraints:

### ICD-10 builder (diagnosis)

- **Purpose:** Chief complaint / diagnosis codes for ePCR and billing; NEMSIS allows ICD-10 where specified.
- **Constraints:** Only codes that are valid for NEMSIS (e.g. state/accepted ICD-10 subset) and that you add or approve.
- **Founder actions:** Add new ICD-10 codes, set display text, link to NEMSIS element (e.g. chief complaint), activate/deactivate.
- **Implementation:** Table `terminology_builder` (or equivalent) with `code_set='icd10'`, `code`, `description`, `nemsis_element_ref`, `org_id`, `active`. API: list/add/update/remove.

### SNOMED builder (interventions)

- **Purpose:** Procedures/interventions in ePCR; map to NEMSIS where SNOMED is accepted.
- **Constraints:** NEMSIS intervention/procedure elements; only SNOMED concepts you add or approve.
- **Founder actions:** Add SNOMED concepts for interventions, set display text, map to NEMSIS procedure element, activate/deactivate.
- **Implementation:** Same table with `code_set='snomed'`, `use_case='intervention'`, `nemsis_element_ref`.

### RXNorm builder (medications)

- **Purpose:** Medications in ePCR and billing; NEMSIS medication elements.
- **Constraints:** RXNorm concepts that are valid for NEMSIS medication fields; only concepts you add or approve.
- **Founder actions:** Add RXNorm codes, set display text, map to NEMSIS medication element, activate/deactivate.
- **Implementation:** Same table with `code_set='rxnorm'`, `use_case='medication'`, `nemsis_element_ref`.

**100% target:** Founder-managed ICD-10, SNOMED, and RXNorm builders with NEMSIS element references; ePCR and billing suggest from these lists; ability to add new ones and adjust wording.

---

## 4. Third-party billing import

You need to **import data for third-party billing** (e.g. bring in runs/claims from another system so you can bill or hand off to a third-party biller).

**Supported import formats (target):**

| Format | Use case | Endpoint (target) |
|--------|----------|--------------------|
| CSV (runs/claims) | Bulk import runs with patient, trip, payer | `POST /api/founder/billing/import/csv` |
| JSON (runs/claims) | Same as CSV; structured | `POST /api/founder/billing/import/json` |
| 837P (X12) | Inbound claim from another system | `POST /api/founder/billing/import/837p` |
| EDI 837I/837P | Institutional/professional claim | `POST /api/founder/billing/import/edi` |

**Data landed:** Imported runs create or update ePCR/billing-adjacent records (e.g. patient, trip, claim stub) so they appear in your billing queue and can be submitted via Office Ally or exported for third-party use.

**100% target:** At least one format (e.g. CSV or JSON) fully wired; 837P/EDI as next phase; audit log for every import.

---

## 5. Agency data export (portability)

Agencies must be able to **export all their data** if they leave for another company.

**Export package (target):**

- **ePCR:** All patients, records, vitals, medications, narrative (anonymized or per your policy).
- **Billing:** Claims, invoices, payments, statements (IDs and amounts; no internal secrets).
- **Fire/NFIRS:** Incidents, timelines, exports (NFIRS records).
- **Comms:** Audit trail of communications (as permitted by retention policy).
- **Documents:** Links or copies of stored documents (e.g. founder documents, billing PDFs).

**Format:** Single ZIP or JSON package per org (or per agency) with a manifest; optional CSV/Excel for billing and ePCR summary.

**Endpoint (target):** `GET /api/founder/agency-export?org_id=...` or `POST /api/founder/agency-export` (founder only) returning a download link or stream.

**100% target:** One-click (or one-request) export of all agency data in a structured, portable format; documented schema; no lock-in.

---

## 6. Export matrix (100% target)

| Export type | Format | Compliance | Status |
|-------------|--------|------------|--------|
| ePCR → NEMSIS | XML (NEMSIS 3.x) | NEMSIS | Payload today; full XML + state submit in progress |
| ePCR → State (WI) | State-specified (e.g. XML) | NEMSIS / Wisconsin | Endpoint config; wiring in progress |
| Fire → NFIRS | JSON/XML (NFIRS 5.0) | NFIRS | Implemented |
| Billing → CMS / 837P | X12 837P, Office Ally | CMS | Implemented |
| Agency data → portable | ZIP/JSON + manifest | — | Spec defined; endpoint to be implemented |
| Third-party billing in | CSV/JSON/837P | — | Spec defined; import endpoint to be implemented |

---

## 7. 100% completion checklist

Use this to drive everything to 100%:

- [ ] **NEMSIS:** Full 3.x XML from ePCR; Wisconsin state submission URL configured and tested.
- [ ] **NFIRS:** All required modules in export; validation against NFIRS 5.0.
- [ ] **CMS:** Billing audit trail and export verified for CMS audits.
- [ ] **Terminology builders:** ICD-10 (NEMSIS-constrained), SNOMED (interventions), RXNorm (medications); founder add/remove/adjust; ePCR/billing use these lists.
- [ ] **Third-party billing import:** CSV/JSON (and optionally 837P) import wired and audited.
- [ ] **Agency data export:** Full export endpoint and package format implemented and documented.
- [ ] **Wisconsin:** Default WI, Wisconsin billing and NEMSIS state config wired; certification checklist completed with Wisconsin EMS.

Once the above are done, the platform is at **100%** for NEMSIS, NFIRS, CMS, Wisconsin certification, terminology builders, third-party billing import, and agency data export.
