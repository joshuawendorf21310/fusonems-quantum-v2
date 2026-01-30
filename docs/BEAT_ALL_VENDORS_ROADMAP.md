# Beat All Vendors — Roadmap

**Goal:** Do everything Zoll, ESO, First Due, FlightVector, ImageTrend, Traumasoft (and others) can do, **but better**—and add differentiators they don’t have. This doc is the single backlog for “beat all vendors” work.

**How to use:** Pick by priority (P0 → P1 → P2) or by domain. Every item should pass the [Product Mandate](PRODUCT_MANDATE.md) ship checklist before marking done.

---

## Status legend

| Status | Meaning |
|--------|--------|
| **Done** | Implemented and meets mandate (better than incumbents, no generic UI). |
| **Partial** | Started; needs completion or wiring (e.g. real data, UI, config). |
| **Not started** | Direction clear; not built. |

**Priority:** P0 = must-have to beat vendors in that area; P1 = strong differentiator; P2 = nice-to-have.

---

## 1. Billing (Fastest at Billing + Sole Biller)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| Transport complete → billing record auto-created | Done | P0 | CAD bridge `handle_transport_completed`. |
| Claim creation from ePCR/patient (one platform) | Done | P0 | `POST /api/billing/claims` with `epcr_patient_id`. |
| Office Ally / 837P batch submission | Done | P0 | `office_ally_sync`, billing_router. |
| Ready check + denial-risk before submit | Done | P0 | `ready_check`, assist snapshot. |
| **Billing speed metrics** (transport→claim→submitted timestamps) | Not started | P0 | [FASTEST_AT_BILLING](billing/FASTEST_AT_BILLING.md). |
| **Billing speed dashboard** (avg/min/max, first-pass rate) | Done | P0 | Billing dashboard speed section; Founder/billing analytics. |
| **Auto-claim creation** (optional when ePCR finalized + ready-check passes) | Not started | P1 | Configurable per org. |
| Missing facesheet: AI call or fax (request + receive) | Partial | P0 | Request + inbound fax done; [outbound call/fax](billing/FACESHEET_CALL_OR_FAX.md) optional. |
| **Outbound call to facility** when facesheet missing (FacilityContact phone) | Partial | P1 | IVR/AI intent recorded; Telnyx outbound call optional. |
| **Outbound fax request** from “Request facesheet” (FacilityContact fax) | Done | P1 | `POST /api/billing/facesheet/send-fax`; FACESHEET_REQUEST_FAX_MEDIA_URL. |
| Sole biller: AI + one queue (docs + UI callout) | Done | P0 | [SOLO_BILLER_SETUP](../SOLO_BILLER_SETUP.md), dashboard copy, .env.example. |

---

## 2. ePCR + NEMSIS (Founder vs ImageTrend/Zoll/ESO/First Due)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| ePCR patient, vitals, meds, narrative, NEMSIS mapper | Done / Partial | P0 | [EPCR_NEMSIS_AND_VENDOR_PARITY](founder/EPCR_NEMSIS_AND_VENDOR_PARITY.md). |
| Validation rules + visibility builder | Done | P0 | EpcrVisibilityRule, validation. |
| Protocol pathways, protocol on record | Done | P0 | |
| **Full NEMSIS XML** from real ePCR (all sections) | Done | P0 | `GET /api/epcr/records/{id}/exports/nemsis` returns XML from element map (schematron_service). |
| **State submission** (real endpoints, config, workflow UI) | Done | P0 | `POST /api/epcr/records/{id}/submit-to-state`; NemsisRecordActions on ePCR detail (Export NEMSIS XML + Submit to state). |
| **Founder terminology builder** (ICD-10, RXNorm, SNOMED add/remove/adjust) | Done | P0 | `/founder/terminology`; list/add/edit/delete; AI suggest; ePCR suggest uses it. |
| **AI suggests for codes** in ePCR (and billing) using terminology + Ollama | Done | P0 | `POST /api/epcr/terminology/suggest`; do_suggest_terminology; Ollama billing explain. |
| Offline ePCR + sync | Partial | P1 | OfflineSyncManager, queue. |
| Multi-org, per-record nemsis_state | Partial | P1 | |

---

## 3. Fire / Preplans (First Due–level)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| Preplans, hydrants, inspections | Partial | P0 | Fire RMS; complete CRUD + field use. |
| NFIRS export/reporting | Partial | P1 | Fire incident reporting. |
| Fire-specific dashboards and workflows | Partial | P1 | Agency/role-specific. |

---

## 4. HEMS (FlightVector–level)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| HEMS missions, handoff, charts | Done / Partial | P0 | hems_router, HemsHandoff. |
| **Flight planning, weather** | Not started | P0 | [EMS MDT gaps](../EMS_MDT_COMPETITIVE_ANALYSIS.md): weather critical for HEMS. |
| Crew/aircraft scheduling | Partial | P1 | |
| One platform: HEMS + ePCR + CAD + billing | Partial | P0 | Integrate, not silos. |

---

## 5. MDT / CAD (Crew experience)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| CAD incidents, units, dispatch | Done / Partial | P0 | incident_router, cad_router. |
| Active incidents, unit status for dashboard | Done | P0 | |
| **Voice dictation / speech-to-text** for PCR | Done | P0 | NarrativeWithDictation on ePCR new page narrative; Web Speech API. |
| **Weather overlay** (MDT/map) | Not started | P1 | Critical for HEMS; absent in incumbents. |
| **Traffic data** (routing) | Not started | P2 | |
| **Hospital bed availability** (real-time) | Not started | P1 | No vendors have it. |
| Geofencing, auto-status by location | Partial | P1 | MDT PWA. |
| Offline map caching | Partial | P1 | |

---

## 6. AI / Voice (Differentiators)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| Ollama: billing explain, IVR, QA | Done | P0 | Sole biller + IVR. |
| AI narrative generation (ePCR, handoff) | Done / Partial | P0 | narrative_generator, self_hosted_ai. |
| **AI co-pilot** (contextual suggestions, auto-complete narratives) | Partial | P0 | Extend Ollama use in ePCR. |
| **Voice documentation** (hands-free PCR) | Not started | P0 | Major industry gap. |
| AI suggests for ICD-10/RXNorm/SNOMED | Planned | P0 | Terminology builder + wire. |

---

## 7. Analytics (Data that drives decisions)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| Reporting widgets, dashboard builder | Partial | P0 | Founder dashboard. |
| **“So what?” actions** (not just charts) | Not started | P0 | Product Mandate principle. |
| Response times, outcomes, NFIRS, revenue | Partial | P1 | |
| Billing speed metrics + dashboard | Done | P0 | See §1; `/api/billing/console/speed` + billing dashboard. |

---

## 8. Integrations (One source of truth)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| **OCR** (equipment screens, vitals) — no device integration | Done / Partial | P0 | Our stack. |
| **Metriport** (patient information) | Done | P0 | Demographics, insurance, FHIR. |
| Hospital handoff (HL7/FHIR send) | Partial | P1 | advanced_features FHIRClient; handoff report. |
| State registries (NEMSIS, NFIRS submit) | Partial | P0 | See §2. |
| BAA tracking (all PHI vendors) | Partial | P0 | [BAA_AND_BREACH](compliance/BAA_AND_BREACH.md). |

---

## 9. Patient Portal / CareFusion

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| Patient bills, payments (real API) | Partial | P1 | Backend exists; frontend wire. |
| CareFusion provider/patient flows (real data) | Partial | P2 | Some routes stubbed. |

---

## 10. Visuals (UI/UX — no generic, beat all vendors)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| **Design system** (tokens: charcoal, orange, red; FusionCare/TransportLink) | Done | P0 | `globals.css` tokens. |
| **No placeholder copy** in shipped UI (real labels, real workflows) | Partial | P0 | Product Mandate principle; audit pages. |
| **Billing dashboard** (cards, speed, sole biller callout) | Done / Partial | P0 | Speed section + metrics. |
| **Compliance/BAA page** (vendor list + status, not generic) | Done | P0 | BAA vendor table; link Founder; [VISUALS_AND_SECURITY](VISUALS_AND_SECURITY.md). |
| **Founder dashboards** (widgets, analytics, “so what?” actions) | Done | P0 | Reporting widgets; "So what? — Next actions" quick-link panel. |
| **Agency/role-specific** screens (fire vs EMS vs HEMS vs billing) | Partial | P0 | Role-based UI; no one-size-fits-all. |
| **Accessibility** (focus, contrast, labels) | Partial | P1 | Audit key flows. |
| **Mobile/tablet** (billing, ePCR, MDT) | Partial | P1 | Responsive; PWAs. |

---

## 11. Security (production-grade from day one)

| Item | Status | Priority | Notes |
|------|--------|----------|--------|
| **Auth** (JWT, roles, MFA where required) | Done | P0 | core/auth, require_roles, require_mfa. |
| **Rate limiting** (auth, API) | Done | P0 | AUTH_RATE_LIMIT_PER_MIN, config. |
| **No hardcoded secrets** (env vars, redacted docs) | Done | P0 | .env.example; PRODUCTION_STATUS redacted. |
| **BAA tracking** (vendor list, status, renewal) | Partial | P0 | [BAA_AND_BREACH](compliance/BAA_AND_BREACH.md); BAA page. |
| **Audit logs** (PHI access, billing, auth events) | Done / Partial | P0 | audit_event, ForensicAuditLog, event_type. |
| **Backup/DR/monitoring** (docs + runbook) | Done | P0 | [BACKUP_DR_MONITORING](operations/BACKUP_DR_MONITORING.md). |
| **CSRF / webhook signature** (Telnyx, Stripe) | Done | P0 | verify_telnyx_signature, etc. |
| **Encryption at rest** (sensitive fields, storage) | Done | P1 | STORAGE_ENCRYPTION_KEY, DOCS_ENCRYPTION_KEY; [ENCRYPTION](operations/ENCRYPTION.md). |

---

## 12. Complete All — master checklist

Use this to track “complete all enhancements, visuals, security.”

- **Billing:** §1 — Speed metrics + dashboard (API + UI), auto-claim optional, outbound call/fax facesheet.
- **ePCR/NEMSIS:** §2 — Full NEMSIS XML + state submission done; terminology builder, AI suggests next.
- **Fire:** §3 — Preplans/hydrants/NFIRS complete; fire dashboards.
- **HEMS:** §4 — Flight planning, weather, one platform.
- **MDT/CAD:** §5 — Voice dictation, weather overlay, hospital bed, geofencing.
- **AI/Voice:** §6 — AI co-pilot in ePCR, voice documentation.
- **Analytics:** §7 — “So what?” actions, billing speed dashboard.
- **Integrations:** §8 — Hospital handoff send, state submit, BAA tracking UI.
- **Patient/CareFusion:** §9 — Wire real API for bills/payments.
- **Visuals:** §10 — No placeholder; BAA vendor table; agency/role-specific; a11y.
- **Security:** §11 — BAA dashboard, audit coverage, encryption documented.

---

## 13. Next 10 actions (recommended order)

1. ~~**Billing speed metrics**~~ — Done: `GET /api/billing/console/speed`; billing dashboard speed section.
2. ~~**Billing speed dashboard**~~ — Done: Founder/billing UI speed section.
3. ~~**Full NEMSIS XML**~~ — Done: `GET /api/epcr/records/{id}/exports/nemsis`; `POST /api/epcr/records/{id}/submit-to-state`.
4. ~~**State submission workflow**~~ — Done: NemsisRecordActions (Export NEMSIS + Submit to state + status). Configurable endpoints (org/founder); “Submit to state” action and status.
5. ~~**Founder terminology builder**~~ — Done: `/founder/terminology` page; list/add/edit/delete ICD-10, SNOMED, RXNorm; AI suggest; wire to ePCR suggest API.
6. ~~**AI suggests in ePCR**~~ — Done: `POST /api/epcr/terminology/suggest`; do_suggest_terminology.
7. ~~**Outbound fax send**~~ — Done: `POST /api/billing/facesheet/send-fax`; FacesheetRetriever.send_facesheet_request_fax; FACESHEET_REQUEST_FAX_MEDIA_URL.
8. **Outbound call to facility** (facesheet) — When facility phone exists, trigger Telnyx outbound call with AI script.
9. **Voice dictation** — Speech-to-text for PCR narrative (browser or app); wire to ePCR narrative field.
10. **Weather overlay** — MDT or map: weather layer (e.g. API); HEMS differentiation.

---

## References

- [Product Mandate](PRODUCT_MANDATE.md) — Goal, stack, ship checklist.
- [Visuals & Security](VISUALS_AND_SECURITY.md) — UI/UX and security checklist.
- [Fastest at Billing](billing/FASTEST_AT_BILLING.md) — Billing speed criteria.
- [Facesheet: Call or Fax](billing/FACESHEET_CALL_OR_FAX.md) — Missing facesheet flows.
- [EPCR, NEMSIS & Vendor Parity](founder/EPCR_NEMSIS_AND_VENDOR_PARITY.md) — Founder vs ImageTrend/Zoll/ESO/First Due.
- [EMS MDT Competitive Analysis](../EMS_MDT_COMPETITIVE_ANALYSIS.md) — 10 vendors, gaps, differentiation.
- [Comprehensive Gap Analysis](../COMPREHENSIVE_GAP_ANALYSIS.md) — Maturity, competitive gaps.

---

*Last updated: January 2026. Revisit when completing items or adding new “beat vendors” goals.*
