# ePCR, NEMSIS & State Export — Founder Guide

## Can I export to NEMSIS and states?

**Yes, in part.** Here’s what exists and what to finish.

### What’s implemented

1. **NEMSIS payload on finalize**  
   When an ePCR record is finalized (`POST /api/epcr/records/{id}/post`), the backend:
   - Runs validation (rule engine, NEMSIS validation result stored).
   - Calls `NEMSISExporter.export_record_to_nemsis(record)` and gets a payload with:
     - `record_id`, `nemsis_version` (e.g. 3.5.1), `state` (e.g. WI), `patient_id`, `incident_number`, `eDisposition.24`, `protocol_pathway`.
   - That payload is **built** and logged; it is **not** yet sent to an external system.

2. **Record-level state**  
   Each ePCR record has:
   - `nemsis_version` (default `3.5.1`)
   - `nemsis_state` (default `WI`)  
   So you can assign version and state per record.

3. **State submission skeleton**  
   `NEMSISSubmissionService` (in `backend/services/billing/automation_services.py`) has:
   - `prepare_nemsis_submission(epcr_id, state_code)` — validation + XML preview.
   - `submit_to_state(epcr_id, state_code, xml_content)` — HTTP POST to a state endpoint.
   - Placeholder state endpoints (e.g. CA, TX, FL) and **stub ePCR data** (not yet wired to real `EpcrRecord`/Patient).

### What’s left to “export to NEMSIS and states”

1. **NEMSIS XML from real ePCR**  
   - Expand `NEMSISExporter` (or add a NEMSIS 3.x XML generator) so it maps **full** ePCR data (patient, vitals, medications, procedures, disposition, etc.) into NEMSIS 3.x XML, not just the small current payload.
2. **State endpoints and config**  
   - Replace placeholder URLs with real state registry/submission URLs (or config-driven endpoints).
   - Add founder/org config for which states you submit to and the correct URLs/credentials if required.
3. **Wiring submission to real data**  
   - `NEMSISSubmissionService._get_epcr_data()` should load real `EpcrRecord` + Patient (and related) from the DB instead of returning stub data.
4. **Submission workflow in the app**  
   - UI/flow for “Export to NEMSIS” / “Submit to state” (e.g. from founder dashboard or ePCR finalize), plus status and error handling.

So: **you can already “export” in the sense of building a NEMSIS-oriented payload and storing state/version; full “export to NEMSIS and states” means completing the XML, real data, and state submission wiring above.**

---

## Founder terminology: AI suggests for RXNorm, SNOMED, ICD-10 (add/remove/adjust)

You want:
- **AI suggests** for RXNorm, SNOMED, and ICD-10 in the ePCR (and billing) flow.
- Ability to **add, remove, and adjust wording** of those suggestions from the founder dashboard.

### Current state

- **ICD-10:** Billing assist uses **keyword heuristics** only (e.g. chest → R07.9, respiratory → J96.00). No full dataset; no founder-editable list in the dashboard.
- **SNOMED / RXNorm:** No dataset or API wired yet; claims export returns empty `snomed` / `rxnorm` arrays. Builder health shows “SNOMED/RXNorm not loaded.”
- **ePCR:** NEMSIS mapper and validation exist; no dedicated “terminology suggest” UI or founder-managed phrases for RXNorm/SNOMED/ICD-10 in ePCR yet.

### Recommended direction (founder dashboard “does everything … but better”)

1. **Terminology builder in founder dashboard**
   - **Lists per code set:** e.g. “ICD-10 suggestions”, “RXNorm suggestions”, “SNOMED suggestions.”
   - Each row: code (or concept id), display text, optional alternate wording, active/inactive.
   - Founder can **add** new suggestions, **remove** (or deactivate), and **adjust wording** (display text, aliases).
2. **AI suggests in ePCR (and billing)**
   - When a user is in ePCR (e.g. diagnosis, medications, procedures), the app calls an API that:
     - Uses narrative/structured input + optional AI (e.g. Ollama) to propose codes.
     - Merges founder-managed suggestions (from the terminology lists) with any dataset/API (ICD-10, RXNorm, SNOMED when loaded).
   - Same idea for billing: coding suggestions should respect founder wording and overrides.
3. **Config for datasets/APIs**
   - Optional: `ICD10_API_URL` / `ICD10_DATASET_LOADED`, `RXNORM_API_URL`, `SNOMED_API_URL` (or similar) so “full” datasets can be used when you add them, while founder-defined phrases still override or extend.

Implementing the above will give you “AI suggests” for RXNorm, SNOMED, and ICD-10 with full founder control over add/remove/adjust wording from the founder dashboard.

---

## Founder dashboard vs ImageTrend, Zoll, ESO, FireDue

Goal: **Founder dashboard to do everything ImageTrend, Zoll, ESO, FireDue can do, but better.**

Below is a high-level checklist. “Done” = we have it in code or design; “Partial” = started but not complete; “Planned” = direction clear, not built.

| Area | ImageTrend / Zoll / ESO / FireDue | FusionEMS Quantum (founder) | Status |
|------|-----------------------------------|------------------------------|--------|
| ePCR (patient, vitals, meds, narrative) | Full ePCR with NEMSIS-aligned fields | Patient, vitals, meds, narrative, NEMSIS mapper, validation | Done / Partial |
| NEMSIS export | Export to NEMSIS format / state | Payload on finalize; full XML + state submit to be completed | Partial |
| State submission | Submit to state EMS registry | Skeleton (prepare + submit); need real data + endpoints | Partial |
| Validation / rule builder | Configurable validation rules | Validation rules + ePCR validation rules + visibility rules | Done |
| Reporting / analytics | Standard and custom reports | Reporting widgets, dashboard builder, exports | Partial |
| Protocols / pathways | Protocol selection, pathways | Protocol pathways, protocol selection on record | Done |
| Terminology (ICD-10, RXNorm, SNOMED) | Built-in code sets, sometimes customizable | Heuristics (ICD-10); SNOMED/RXNorm not loaded; founder terminology builder planned | Planned |
| AI / smart suggest | Some vendors have limited AI | Ollama-based AI (billing explain, IVR); AI suggests for codes planned | Partial |
| Configurable visibility | Field-level visibility | Visibility builder (EpcrVisibilityRule) | Done |
| Multi-org / multi-state | Multi-org, state-specific | Multi-org; per-record `nemsis_state`; state endpoints configurable | Partial |
| Offline / sync | Offline ePCR, sync when online | OfflineSyncManager, queue record | Partial |
| Billing integration | Billing from ePCR | Billing claims, assist, Office Ally, Stripe | Done / Partial |

To “do everything they do but better,” focus on:
1. **Completing NEMSIS export and state submission** (XML from real ePCR, configurable state endpoints, submission workflow).
2. **Founder terminology builder** (add/remove/adjust RXNorm, SNOMED, ICD-10 suggestions) and wiring AI suggests in ePCR (and billing) to those lists.
3. **Full SNOMED/RXNorm/ICD-10 datasets or APIs** where you want richer suggestions, while keeping founder wording as the source of truth for overrides and custom phrases.

---

## Summary

- **Export to NEMSIS:** Yes — payload is built on finalize; next step is full NEMSIS XML and, if you want, a dedicated “Export to NEMSIS” action.
- **Export to states:** Partially — submission flow and placeholder endpoints exist; need real ePCR → XML and real state registry URLs/config.
- **AI suggests for RXNorm, SNOMED, ICD-10 with add/remove/adjust:** Planned; implement via a **terminology builder** in the founder dashboard and wire ePCR (and billing) to use those suggestions plus any datasets/APIs.
- **Do everything ImageTrend, Zoll, ESO, FireDue do but better:** Use the checklist above; priorities are NEMSIS/state export, terminology builder, and dataset/API integration for codes.
