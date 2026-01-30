# 500 Enhancements — Master List

**Goal:** Real-life ready, 100% completed, integrated frontend + backend. Minimal external integration; built-in where possible.

**Legend:** **B** = Built-in | **I** = Integration | **D** = Done | **P** = Partial | **N** = Not started | **P0/P1/P2** = Priority

---

## 1. AI (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 1 | Ollama narrative generation (ePCR, handoff) | B | D | P0 |
| 2 | Ollama billing explain / IVR biller helper | B | D | P0 |
| 3 | AI terminology suggest (ICD-10, SNOMED, RXNorm) | B | D | P0 |
| 4 | AI protocol suggestion on finalize | B | P | P0 |
| 5 | AI chief complaint → code suggest in ePCR UI | B | P | P0 |
| 6 | Voice-to-text for PCR narrative (Web Speech API or built-in) | B | D | P0 |
| 7 | AI co-pilot contextual suggestions in ePCR | B | N | P0 |
| 8 | AI denial reason analysis and fix suggestions | B | N | P1 |
| 9 | AI QA score explanation | B | N | P1 |
| 10 | AI handoff summary (SBAR) generator | B | P | P1 |
| 11 | AI dispatch narrative from CAD event | B | N | P1 |
| 12 | AI incident type suggestion from location/complaint | B | N | P1 |
| 13 | AI crew assignment suggestion (skills, location) | B | N | P1 |
| 14 | AI schedule conflict detection | B | N | P1 |
| 15 | AI training recommendation from gaps | B | N | P2 |
| 16 | AI fire preplan summary from structure | B | N | P2 |
| 17 | AI medication interaction check (ePCR) | B | N | P2 |
| 18 | AI vital trend alert (e.g. declining BP) | B | N | P2 |
| 19 | AI narrative completeness check | B | N | P2 |
| 20 | AI duplicate patient detection | B | N | P2 |
| 21 | AI fax document classification | B | P | P2 |
| 22 | AI facesheet field extraction (OCR + NLP) | B | P | P2 |
| 23 | AI prior-auth wording suggestion | B | N | P2 |
| 24 | AI appeal letter draft from denial | B | N | P2 |
| 25 | AI patient portal FAQ answer | B | N | P2 |
| 26 | AI FusionCare visit note suggestion | B | N | P2 |
| 27 | AI training quiz question generation | B | N | P2 |
| 28 | AI compliance alert explanation | B | N | P2 |
| 29 | AI audit log anomaly detection | B | N | P2 |
| 30 | AI predictive unit availability | B | N | P2 |
| 31 | AI response time prediction | B | N | P2 |
| 32 | AI hospital diversion recommendation | B | N | P2 |
| 33 | AI crew fatigue risk indicator | B | N | P2 |
| 34 | AI equipment maintenance prediction | B | N | P2 |
| 35 | AI supply reorder suggestion | B | N | P2 |
| 36 | AI NEMSIS validation fix suggestion | B | N | P2 |
| 37 | AI NFIRS narrative suggestion | B | N | P2 |
| 38 | AI HEMS weather risk summary | B | N | P2 |
| 39 | AI telehealth triage suggestion | B | N | P2 |
| 40 | AI agency report narrative | B | N | P2 |
| 41 | AI multi-language chief complaint translation | B | N | P2 |
| 42 | AI signature verification | B | N | P2 |
| 43 | AI duplicate run detection | B | N | P2 |
| 44 | AI outlier charge flagging | B | N | P2 |
| 45 | AI payer mix optimization hint | B | N | P2 |
| 46 | AI staffing level suggestion | B | N | P2 |
| 47 | AI MCI resource suggestion | B | N | P2 |
| 48 | AI CCT protocol match | B | N | P2 |
| 49 | AI ePCR section auto-expand on error | B | N | P2 |
| 50 | AI “what’s next” step in every workflow | B | N | P2 |

---

## 2. ePCR (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 51 | Patient demographics (NEMSIS-aligned) | B | D | P0 |
| 52 | Vitals entry + NEMSIS mapping | B | D | P0 |
| 53 | Medications / interventions / procedures | B | D | P0 |
| 54 | Chief complaint + code (terminology) | B | D | P0 |
| 55 | Narrative + AI suggest | B | P | P0 |
| 56 | Validation rules + Schematron | B | D | P0 |
| 57 | Visibility builder (field-level) | B | D | P0 |
| 58 | Protocol pathways + selection on record | B | D | P0 |
| 59 | NEMSIS export XML (full element map) | B | D | P0 |
| 60 | State submission (submit-to-state) | B | D | P0 |
| 61 | Founder terminology builder (ICD-10, SNOMED, RXNorm) | B | D | P0 |
| 62 | ePCR list + filters + pagination | B | D | P0 |
| 63 | ePCR create (desktop + tablet EMS/Fire/HEMS) | B | D | P0 |
| 64 | ePCR detail + timeline | B | P | P0 |
| 65 | ePCR finalize + validation UI | B | P | P0 |
| 66 | Export to NEMSIS button + download XML | B | D | P0 |
| 67 | Submit to state button + status | B | D | P0 |
| 68 | Terminology suggest in chief complaint field | B | D | P0 |
| 69 | Terminology suggest in impression/meds | B | P | P0 |
| 70 | Offline ePCR + sync queue | B | P | P1 |
| 71 | Multi-org, per-record nemsis_state | B | P | P1 |
| 72 | CCT-specific sections | B | P | P1 |
| 73 | Pediatric weight/age validation | B | P | P1 |
| 74 | OB section (if applicable) | B | N | P1 |
| 75 | Signature capture + lock | B | P | P1 |
| 76 | Copy previous run (templates) | B | N | P1 |
| 77 | ePCR PDF export (run report) | B | N | P1 |
| 78 | ePCR print view | B | N | P1 |
| 79 | Attach image/OCR to section | B | P | P1 |
| 80 | Repeat vitals overlay | B | N | P1 |
| 81 | QA indicator on record | B | N | P1 |
| 82 | Read-only view (audit) | B | N | P1 |
| 83 | ePCR clone for MCI | B | N | P2 |
| 84 | ePCR merge (duplicate run) | B | N | P2 |
| 85 | ePCR version history | B | N | P2 |
| 86 | ePCR redact for release | B | N | P2 |
| 87 | ePCR bulk export (date range) | B | N | P2 |
| 88 | ePCR search (full-text) | B | N | P2 |
| 89 | ePCR dashboard (recent, stats) | B | D | P0 |
| 90 | ePCR validation errors inline | B | P | P0 |
| 91 | ePCR NEMSIS element ref on fields | B | N | P2 |
| 92 | ePCR auto-save draft | B | N | P1 |
| 93 | ePCR device time vs server time warning | B | P | P1 |
| 94 | ePCR handoff summary one-tap | B | N | P1 |
| 95 | ePCR hospital notification status | B | N | P1 |
| 96 | ePCR billing claim link | B | N | P1 |
| 97 | ePCR CAD incident link | B | P | P1 |
| 98 | ePCR crew member assignment | B | N | P2 |
| 99 | ePCR vehicle/unit on record | B | N | P2 |
| 100 | ePCR mileage/destination | B | P | P1 |

---

## 3. CAD (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 101 | Incidents CRUD + list | B | D | P0 |
| 102 | Active incidents endpoint | B | D | P0 |
| 103 | Unit status endpoint | B | D | P0 |
| 104 | New incident modal → POST | B | D | P0 |
| 105 | CAD dashboard (active, units) | B | D | P0 |
| 106 | Incident detail + timeline | B | P | P0 |
| 107 | Unit assignment to incident | B | P | P0 |
| 108 | Dispatch event log | B | P | P0 |
| 109 | Transport complete → billing hook | B | D | P0 |
| 110 | Requesting/receiving facility on incident | B | D | P0 |
| 111 | Incident status workflow (pending, en route, on scene, etc.) | B | P | P0 |
| 112 | CAD map (incidents, units) | B | N | P1 |
| 113 | Geofencing (auto-status by location) | B | P | P1 |
| 114 | Silent dispatch (no radio) | B | N | P1 |
| 115 | Incident priority/type | B | P | P1 |
| 116 | Incident notes/comments | B | N | P1 |
| 117 | Incident timeline (audit) | B | P | P1 |
| 118 | Unit availability (in quarters, on call, etc.) | B | P | P1 |
| 119 | Multi-CAD bridge (socket) | B | P | P1 |
| 120 | CAD ↔ ePCR link (incident ↔ record) | B | P | P1 |
| 121 | CAD ↔ CrewLink trip sync | B | P | P1 |
| 122 | Incident reassignment | B | N | P1 |
| 123 | Incident merge (duplicate) | B | N | P2 |
| 124 | Incident cancel/void | B | N | P1 |
| 125 | Incident print card | B | N | P2 |
| 126 | CAD call taker script | B | N | P2 |
| 127 | CAD EMD protocol display | B | N | P2 |
| 128 | CAD caller ID / callback | B | N | P2 |
| 129 | CAD response time SLA tracking | B | N | P1 |
| 130 | CAD unit rotation (round-robin) | B | N | P2 |
| 131 | CAD mutual aid request | B | N | P2 |
| 132 | CAD MCI mode (multiple patients) | B | N | P2 |
| 133 | CAD weather overlay on map | B | N | P1 |
| 134 | CAD traffic layer | B | N | P2 |
| 135 | CAD hospital bed status (if integrated) | I | N | P1 |
| 136 | CAD predictive demand | B | N | P2 |
| 137 | CAD unit recommend by location/skill | B | N | P1 |
| 138 | CAD incident export (CSV/Excel) | B | N | P2 |
| 139 | CAD analytics (response time, volume) | B | N | P1 |
| 140 | CAD filters (date, status, unit) | B | N | P1 |
| 141 | CAD search (address, incident #) | B | N | P1 |
| 142 | CAD bulk status update | B | N | P2 |
| 143 | CAD notification (new incident to unit) | B | N | P1 |
| 144 | CAD escalation (no response) | B | N | P2 |
| 145 | CAD unit OOS (out of service) | B | N | P1 |
| 146 | CAD supervisor override | B | N | P2 |
| 147 | CAD audit log (who dispatched) | B | N | P1 |
| 148 | CAD HL7 receive (hospital ADT) | I | N | P2 |
| 149 | CAD 911 feed (if integration) | I | N | P2 |
| 150 | CAD backup/failover | B | N | P2 |

---

## 4. Billing (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 151 | Claim create from ePCR patient | B | D | P0 |
| 152 | Ready check + denial-risk before submit | B | D | P0 |
| 153 | Office Ally / 837P batch submit | B | D | P0 |
| 154 | Billing speed metrics API | B | D | P0 |
| 155 | Billing speed dashboard (avg, first-pass) | B | D | P0 |
| 156 | Sole biller UI callout | B | D | P0 |
| 157 | Facesheet request (AI call or fax) | B | D | P0 |
| 158 | Inbound fax parse + patient match | B | D | P0 |
| 159 | Auto-claim when ePCR finalized (config) | B | D | P0 |
| 160 | Outbound fax request (facility fax) | B | N | P1 |
| 161 | Outbound call to facility (facesheet) | B | N | P1 |
| 162 | Billing dashboard (cards, speed, facesheet) | B | D | P0 |
| 163 | Claims ready list + submit | B | D | P0 |
| 164 | Call queue (Telnyx) | B | D | P0 |
| 165 | AI assist panel (billing) | B | D | P0 |
| 166 | Denial list + reason | B | D | P0 |
| 167 | Prior auth request/status | B | P | P1 |
| 168 | Insurance verify (Metriport) | B | D | P0 |
| 169 | Patient responsibility + Stripe | B | P | P0 |
| 170 | EOB/ERA parse (835) | B | N | P1 |
| 171 | Remittance advice list | B | N | P1 |
| 172 | Claim status inquiry | B | N | P1 |
| 173 | Appeal packet create | B | N | P2 |
| 174 | Patient statement generate | B | N | P1 |
| 175 | Payment posting (check/CC) | B | N | P1 |
| 176 | Billing analytics (payer mix, aging) | B | P | P1 |
| 177 | Billing export (CSV/Excel) | B | N | P2 |
| 178 | Medical necessity snapshot on claim | B | D | P0 |
| 179 | Demographics snapshot on claim | B | D | P0 |
| 180 | Training mode (no live submit) | B | D | P0 |
| 181 | BAA tracking (vendor list) | B | D | P0 |
| 182 | Billing audit log (claim created, submitted) | B | D | P0 |
| 183 | Claim edit (draft) before submit | B | N | P1 |
| 184 | Claim void/cancel | B | N | P2 |
| 185 | Batch export (837P file download) | B | N | P2 |
| 186 | Clearinghouse ack store | B | N | P1 |
| 187 | First-pass acceptance rate metric | B | D | P0 |
| 188 | Pending claim count | B | D | P0 |
| 189 | Billing org config (NPI, etc.) | B | P | P1 |
| 190 | Payer list (founder-managed) | B | N | P2 |
| 191 | Fee schedule (per procedure) | B | N | P2 |
| 192 | Billing rules (auto-code from narrative) | B | N | P2 |
| 193 | Wisconsin / state-specific rules | B | P | P1 |
| 194 | Solo biller config (founder) | B | D | P0 |
| 195 | Billing AI explain (term, question) | B | D | P0 |
| 196 | Billing lookup (patient/incident) | B | P | P0 |
| 197 | Claim detail page (frontend) | B | P | P0 |
| 198 | Claim review page (facesheet status) | B | D | P0 |
| 199 | Receipt/expense OCR (founder) | B | P | P1 |
| 200 | Billing report (MTD, YTD) | B | N | P1 |

---

## 5. CrewLink (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 201 | Trip list (assignments) | B | P | P0 |
| 202 | Trip detail (pickup, destination, patient) | B | P | P0 |
| 203 | Document upload (facesheet, PCS, AOB) | B | P | P0 |
| 204 | CrewLink login (org/auth) | B | P | P0 |
| 205 | Trip status (en route, on scene, complete) | B | P | P0 |
| 206 | CrewLink ↔ CAD trip sync | B | P | P0 |
| 207 | CrewLink ↔ ePCR link (trip → record) | B | P | P0 |
| 208 | Offline trip cache | B | N | P1 |
| 209 | Trip history (past) | B | N | P1 |
| 210 | Document type (FACESHEET, PCS, AOB, DNR) | B | D | P0 |
| 211 | Scan/camera for document | B | P | P0 |
| 212 | Trip accept/decline | B | N | P1 |
| 213 | Trip notes | B | N | P1 |
| 214 | Trip mileage | B | N | P2 |
| 215 | Trip signature (patient) | B | N | P2 |
| 216 | CrewLink notifications (new trip) | B | N | P1 |
| 217 | CrewLink push (if PWA) | B | N | P2 |
| 218 | Crew availability (on/off) | B | N | P1 |
| 219 | Crew profile (certs, photo) | B | N | P2 |
| 220 | CrewLink facility directory | B | P | P1 |
| 221 | CrewLink map (trip route) | B | N | P1 |
| 222 | CrewLink weather for trip | B | N | P2 |
| 223 | CrewLink traffic ETA | B | N | P2 |
| 224 | CrewLink patient info (from Metriport) | B | N | P1 |
| 225 | CrewLink handoff summary view | B | N | P1 |
| 226 | CrewLink PWA install | B | N | P1 |
| 227 | CrewLink offline queue | B | N | P1 |
| 228 | CrewLink sync status indicator | B | N | P1 |
| 229 | CrewLink dark mode | B | N | P2 |
| 230 | CrewLink accessibility (a11y) | B | N | P2 |
| 231–250 | CrewLink: multi-leg trip, return trip, CCT checklist, vehicle checklist, narcotic log link, crew swap, supervisor view, audit log, export, config | B | N | P2 |

---

## 6. MDT (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 251 | MDT login (org/auth) | B | P | P0 |
| 252 | Active incident list | B | D | P0 |
| 253 | Unit status update | B | P | P0 |
| 254 | Incident detail (address, type, notes) | B | P | P0 |
| 255 | MDT ↔ CAD sync | B | P | P0 |
| 256 | MDT ↔ ePCR open record | B | P | P0 |
| 257 | Geofencing (auto status) | B | P | P1 |
| 258 | MDT map (incidents, units) | B | N | P1 |
| 259 | MDT navigation (to scene) | B | N | P1 |
| 260 | Weather overlay | B | N | P1 |
| 261 | Voice dictation (narrative) | B | N | P0 |
| 262 | MDT offline mode | B | N | P1 |
| 263 | MDT trip history | B | N | P1 |
| 264 | MDT PWA install | B | N | P1 |
| 265 | MDT push (new assignment) | B | N | P1 |
| 266 | MDT hospital list (destinations) | B | N | P1 |
| 267 | MDT traffic ETA | B | N | P2 |
| 268 | MDT OBD-II (if integration) | I | N | P2 |
| 269 | MDT panic button | B | N | P1 |
| 270 | MDT crew messaging | B | N | P1 |
| 271 | MDT status quick buttons | B | P | P0 |
| 272 | MDT timestamp log (en route, on scene) | B | P | P0 |
| 273–300 | MDT: hospital bed, MCI mode, unit swap, supervisor map, audit, config, a11y, dark mode, etc. | B | N | P2 |

---

## 7. Fire (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 301 | Fire incidents (RMS) | B | P | P0 |
| 302 | Preplans CRUD | B | P | P0 |
| 303 | Hydrants CRUD + flow test | B | P | P0 |
| 304 | Inspections CRUD + violations | B | P | P0 |
| 305 | NFIRS export/reporting | B | P | P1 |
| 306 | Fire apparatus + maintenance | B | P | P0 |
| 307 | Fire personnel (certs) | B | P | P1 |
| 308 | Fire dashboard (calls, inspections) | B | P | P0 |
| 309 | Preplan map (locations) | B | N | P1 |
| 310 | Hydrant map | B | N | P1 |
| 311 | Fire run report (ePCR-like) | B | P | P1 |
| 312 | NFIRS state submit | B | N | P1 |
| 313 | Fire incident timeline | B | N | P1 |
| 314 | Fire unit status | B | P | P0 |
| 315 | Fire scheduling (shift) | B | P | P1 |
| 316–350 | Fire: hazmat, MCI, mutual aid, inventory, training, analytics, print, export, config | B | N | P2 |

---

## 8. Schedule (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 351 | Shift calendar view | B | P | P0 |
| 352 | Shift create/edit | B | P | P0 |
| 353 | Assignment (unit/crew to shift) | B | P | P0 |
| 354 | Schedule conflict warning | B | N | P1 |
| 355 | Schedule swap request | B | N | P1 |
| 356 | Schedule publish (week) | B | N | P1 |
| 357 | Schedule import (CSV) | B | N | P2 |
| 358 | Schedule template | B | N | P2 |
| 359 | Time-off request | B | N | P1 |
| 360 | Schedule notification (new shift) | B | N | P1 |
| 361–400 | Schedule: overtime, coverage gap, predictive staffing, integration with HR, export, audit | B | N | P2 |

---

## 9. FusionCare (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 401 | Provider login | B | P | P0 |
| 402 | Patient login | B | P | P0 |
| 403 | Provider dashboard | B | P | P0 |
| 404 | Patient dashboard | B | P | P0 |
| 405 | Appointments list/book | B | P | P0 |
| 406 | Visits (encounters) | B | P | P0 |
| 407 | SOAP note entry | B | P | P0 |
| 408 | Video visit (Jitsi) | B | P | P0 |
| 409 | Patient medications/allergies | B | P | P0 |
| 410 | Provider schedule | B | P | P0 |
| 411 | Patient profile | B | P | P0 |
| 412 | Prescriptions list/create | B | P | P0 |
| 413 | Visit complete workflow | B | P | P0 |
| 414 | Real API (appointments, visits, providers) | B | P | P0 |
| 415 | FusionCare ↔ ePCR link (if same org) | B | N | P2 |
| 416–450 | FusionCare: labs, referrals, clinical summary, CCD export, reminders, a11y, mobile | B | N | P2 |

---

## 10. Training (50 items)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| 451 | Courses list + detail | B | P | P0 |
| 452 | Enrollments (enroll, progress) | B | P | P0 |
| 453 | Assessments (quiz) + submit | B | P | P0 |
| 454 | Certifications list + expiring | B | P | P0 |
| 455 | Training dashboard (my learning) | B | P | P0 |
| 456 | Skill checks | B | P | P0 |
| 457 | Training admin (create course) | B | P | P0 |
| 458 | Training completion certificate | B | N | P1 |
| 459 | Training due/overdue alert | B | N | P1 |
| 460 | Training compliance report | B | N | P1 |
| 461–500 | Training: CE credits, SCORM, video, attachments, role-based catalog, recert reminder, integration with HR certs | B | N | P2 |

---

## 11. Global (cross-cutting)

| # | Item | B/I | Status | P |
|---|------|-----|--------|---|
| - | Auth (JWT, roles, MFA) | B | D | P0 |
| - | Rate limiting | B | D | P0 |
| - | Health check (/health, /healthz) | B | D | P0 |
| - | BAA tracking (vendor table) | B | D | P0 |
| - | Audit log (events) | B | D | P0 |
| - | Backup/DR doc | B | D | P0 |
| - | Encryption at rest (doc) | B | D | P1 |
| - | Design system (tokens) | B | D | P0 |
| - | No placeholder copy (audit) | B | P | P0 |
| - | Agency/role-specific UI | B | P | P0 |
| - | Responsive (mobile/tablet) | B | P | P1 |
| - | Accessibility (focus, contrast) | B | P | P1 |
| - | Global search | B | P | P0 |
| - | Notifications (in-app) | B | P | P0 |
| - | Founder dashboard (widgets) | B | P | P0 |
| - | “So what?” actions on dashboards | B | N | P0 |

---

## Implementation priority (build to 100%)

**Phase 1 (wire frontend + backend, real-life ready):**
1. ePCR: Export NEMSIS + Submit to state buttons on record detail.
2. ePCR: Terminology suggest in chief complaint (call `/api/founder/terminology/suggest` or `/api/epcr/terminology/suggest`).
3. Billing: Outbound fax from Request facesheet (facility lookup + send).
4. Founder/Billing: “So what?” actions widget (Submit to state, Request facesheet, Fix denial).
5. Health: `/health` (done). Encryption doc (done in operations/ENCRYPTION.md if exists).
6. Mark roadmap items Done where implemented.

**Phase 2 (next 50):** Voice dictation stub, weather config, MDT/CrewLink offline, Fire NFIRS submit, Schedule conflict, FusionCare real API everywhere, Training certificate.

**Phase 3 (remaining):** All P2 items, integrations, polish.

---

*Total: 500+ items across AI, ePCR, CAD, Billing, CrewLink, MDT, Fire, Schedule, FusionCare, Training, Global. Build order: Phase 1 → Phase 2 → Phase 3 until 100% completed, integrated, real-life ready.*
