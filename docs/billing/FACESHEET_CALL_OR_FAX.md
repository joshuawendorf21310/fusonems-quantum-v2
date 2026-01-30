# Facesheet: AI Call or Fax When Missing

**Product requirement:** When a facesheet (patient demographics from facility) is missing, the system uses **AI to call** the hospital or **gets the facesheet via fax** (request and/or receive). No manual-only path.

---

## 1. What We Support

| Channel | Role | Implementation |
|--------|------|-----------------|
| **Call** | AI-assisted request to facility | `POST /api/billing/facesheet/request` → `FacesheetRetriever.request_facesheet_from_facility()` → AI (Ollama) generates request script; call summary recorded with intent `facesheet_request`, resolution `awaiting_fax`. Optional: place outbound call to facility when we have facility phone (e.g. `FacilityContact.phone_number` or incident `receiving_facility` lookup). |
| **Fax (receive)** | Get facesheet when facility faxes us | Telnyx webhook `POST /api/telnyx/fax-received` → `TelnyxFaxHandler.store_fax()` → parse facesheet (OCR/key:value), match patient, sync demographics, notify billers. Inbound fax is the primary “get facesheet” path. |
| **Fax (send)** | Request facesheet from facility | When we have facility fax number (`FacilityContact.fax_number` or destination facility lookup), send outbound fax request (e.g. via `POST /api/comms/send/fax` or founder fax) so the hospital can fax the facesheet back. Inbound fax then handled as above. |

---

## 2. Flow: Missing Facesheet

1. **Detect missing:** Billing/claim flow uses `GET /api/billing/facesheet/status/{epcr_patient_id}`. If `present: false` and `missing_fields` non-empty, facesheet is missing.
2. **Request via call or fax:** Biller (or automation) calls `POST /api/billing/facesheet/request` with `epcr_patient_id`.
   - **Call path:** Service uses AI to build the request (e.g. “Request facesheet and fax”); records call summary with intent `facesheet_request` and resolution `awaiting_fax`. Optional extension: initiate outbound call to facility phone when available.
   - **Fax path:** Optional extension: if destination/receiving facility is known and we have a fax number (e.g. from `FacilityContact` or incident), send outbound fax to that facility requesting the facesheet; when they fax back, inbound handler parses and syncs.
3. **Receive fax:** When facility sends a fax, Telnyx hits `/api/telnyx/fax-received`. We parse the fax as a facesheet, match to patient, sync demographics, and notify billers. No manual data entry.
4. **Recheck status:** `GET /api/billing/facesheet/status/{epcr_patient_id}` and claim ready-check reflect updated demographics after sync.

---

## 3. Implementation Hooks

- **Facesheet request (call + AI):** `backend/services/billing/facesheet_router.py` — `POST /request`; `backend/services/billing/facesheet_retriever.py` — `FacesheetRetriever.request_facesheet_from_facility()` (AI via `TelnyxIVRService.route_to_ai_agent`, intent `facesheet_request`).
- **Inbound fax (get facesheet):** `backend/services/telnyx/telnyx_service.py` — `TelnyxFaxHandler.store_fax()`, `extract_facesheet()`, `match_patient()`, `_sync_patient()`; webhook in `backend/services/telnyx/ivr_router.py` or telnyx_router (e.g. `/api/telnyx/fax-received`).
- **Outbound fax (request facesheet):** `POST /api/comms/send/fax`; `backend/services/fax/` (orchestrator, `FacilityContact`). Optional: from `FacesheetRetriever`, look up facility by patient transport destination and send fax request when `FacilityContact.fax_number` exists.
- **Facility contact (phone/fax):** `backend/models/fax.py` — `FacilityContact` (phone_number, fax_number, facility_name, department).

---

## 4. Gaps / Extensions

- **Outbound call to facility:** Today we record “request facesheet” and AI response; we do not yet place an outbound call to the hospital. Extension: when we have facility phone (e.g. from `FacilityContact` or incident `receiving_facility`), trigger Telnyx outbound call with AI script to request facesheet (and optionally ask them to fax it).
- **Outbound fax from facesheet request:** When biller clicks “Request facesheet,” optionally look up destination facility and send an outbound fax request (e.g. “Please fax facesheet for [patient name, DOB] to [our fax]”) when `FacilityContact.fax_number` is available.
- **Auto-request on missing:** When claim ready-check fails due to missing facesheet, optionally auto-trigger “request via call or fax” (configurable per org).

---

## 5. References

- [Product Mandate](../PRODUCT_MANDATE.md) — Better than any vendor; fastest at billing.
- [Fastest at Billing](FASTEST_AT_BILLING.md) — Speed criteria; missing facesheet delays claim submission.
- [RUNBOOK_PHASE1](../../RUNBOOK_PHASE1.md) — Facesheet retrieval, Telnyx, fax webhooks.
- `backend/services/billing/facesheet_retriever.py` — Call + AI request; fax parse via `TelnyxFaxHandler`.
- `backend/services/telnyx/telnyx_service.py` — `TelnyxFaxHandler` (inbound fax, extract_facesheet, match, sync).

---

*Last updated: January 2026.*
