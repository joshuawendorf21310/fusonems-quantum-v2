# Product Mandate: Better and Enhanced Than Any Other Vendor

**Goal:** FusionEMS Quantum v2 will be **better and more enhanced than any other vendor can do**, and **the fastest at billing.** Nothing we ship is generic. Every feature must be best-in-class or we don’t ship it.

**Sole biller:** You may be the only biller. The system is built for that—AI does as much as possible, one queue, no round-robin. See [Solo Biller Setup](SOLO_BILLER_SETUP.md).

---

## 1. What “Better Than Any Vendor” Means

- **Outcome:** Agencies choose us because we do more, faster, and clearer than Zoll, ESO, First Due, FlightVector, ImageTrend, Traumasoft, or anyone else.
- **Method:** One platform, one UX, one data model—ePCR, CAD, fire RMS, HEMS, billing, analytics—with no generic modules and no “good enough” screens.
- **Bar:** For every capability, ask: “What would the best incumbent do?” Then we define how we do it **better** (faster, fewer clicks, one source of truth, or a capability they don’t have).

---

## 2. Our Stack (Non‑Negotiable)

| Need | Our approach | Not |
|------|----------------|-----|
| **Vitals / equipment data** | **OCR** — photo-based equipment screens (monitor, ventilator, meds, blood); auto-populate charts | Device integration (Bluetooth, vendor APIs) |
| **Patient information** | **Metriport** — demographics, insurance, medical history, FHIR | Building our own EHR/patient registry |
| **AI / suggest** | **Ollama** (and planned extensions) — narrative, codes, IVR, QA | Generic third‑party black boxes without control |
| **Compliance / BAA** | Track every PHI vendor; BAA required before PHI | Ad‑hoc vendor onboarding |

Every new feature must align with this stack. No parallel “generic” systems.

---

## 3. Principles for Every Feature

1. **Agency- and role-specific**  
   Fire vs EMS vs HEMS vs IFT: workflows and UI are built for that agency type and role (crew, admin, billing), not a single generic flow.

2. **One source of truth**  
   Patient info from Metriport; vitals/equipment from OCR; incidents from our CAD/ePCR. We don’t duplicate or rebuild what we already have.

3. **Fewer steps, clearer actions**  
   Every flow is measured in steps and clicks. If another vendor does it in N steps, we aim for fewer or one clear action.

4. **Data that drives decisions**  
   Analytics (response times, outcomes, NFIRS, revenue) must answer “so what?” and suggest actions, not just show dashboards.

5. **Production-grade from day one**  
   Auth, rate limits, auditability, BAA, backup/DR. No “we’ll harden it later.”

6. **No filler**  
   No placeholder copy, no generic “Lorem ipsum” flows, no “TODO” in shipped UX. If we don’t have real content or logic, we don’t ship the surface.

---

## 4. Ship Checklist (Every New Feature)

Before marking any feature “done,” confirm:

- [ ] **Better than incumbents:** We can state how it’s better (or at least as good) than Zoll/ESO/First Due/FlightVector/ImageTrend in this area.
- [ ] **Uses our stack:** Uses OCR for equipment/vitals, Metriport for patient info, and existing auth/audit; no new parallel “generic” systems.
- [ ] **Agency/role-specific:** Built for specific agency type(s) and role(s), not a one-size-fits-all screen.
- [ ] **One source of truth:** Reads/writes the canonical system (e.g. Metriport, OCR results, CAD/ePCR); no duplicate stores for the same concept.
- [ ] **Production-ready:** Auth, rate limits, audit trail where applicable; no hardcoded secrets or “admin only” shortcuts in production paths.
- [ ] **No generic UI:** Real labels, real workflows, real validations; no placeholder text or fake buttons in shipped code.

---

## 5. Competitive Bar (Quick Reference)

- **ESO** — ePCR, fire RMS, NFIRS, billing, analytics, EHR integration. We match breadth and exceed on UX, AI, and single-platform consistency.
- **Zoll** — Device integration, ePCR, billing, QA. We exceed with **OCR** (no device lock-in) and Metriport for patient info.
- **First Due** — Preplans, hydrants, NFIRS, inspections. We match fire/field depth and exceed on EMS/HEMS and analytics.
- **FlightVector** — HEMS flight planning, weather, crew/asset scheduling. We match HEMS depth and exceed on integration with ePCR/CAD/billing in one platform.
- **ImageTrend / Traumasoft / others** — We do “everything they do, but better” per [EPCR_NEMSIS_AND_VENDOR_PARITY.md](founder/EPCR_NEMSIS_AND_VENDOR_PARITY.md), and we add AI, OCR, and Metriport as differentiators.

---

## 6. Fastest at Billing

**We will be the fastest at billing.** That means:

- **Time to claim:** Shortest time from transport complete → claim created → submitted to payer (or clearinghouse). We measure and optimize this end-to-end.
- **Automation:** Billing record created automatically on transport complete (CAD bridge); claims ready for submission with minimal manual steps; validation and medical-necessity assist run upfront so we don’t submit then fix.
- **Fewer steps:** One platform (ePCR + CAD + billing): no re-keying, no export/import. Insurance from Metriport; codes from ePCR; claim creation and 837P/Office Ally batch with as few clicks as possible.
- **Denial prevention:** Validation and denial-risk flags before submission so “fast” doesn’t mean “fast to denial.” We aim for first-pass acceptance.
- **Metrics we own:** We track and report: transport complete → claim created (minutes), claim created → submitted (minutes), submission → first response (SLA). We optimize for these.
- **Missing facesheet:** When a facesheet (demographics from facility) is missing, we don’t block on manual follow-up. **AI can call** the hospital (AI-assisted request) or we **get it via fax** (inbound fax parsed and matched; optional outbound fax request to facility). See [Facesheet: Call or Fax](billing/FACESHEET_CALL_OR_FAX.md).

See [Fastest at Billing](billing/FASTEST_AT_BILLING.md) for criteria, automation points, and metrics.

---

## 7. Beat All Vendors Roadmap

- **[Beat All Vendors Roadmap](BEAT_ALL_VENDORS_ROADMAP.md)** — Single backlog for “beat all vendors” work: billing, ePCR/NEMSIS, fire, HEMS, MDT, AI/voice, analytics, integrations. Status (Done/Partial/Not started), priority (P0/P1/P2), and **Next 10 actions** in recommended order.

---

## 8. References

- [Beat All Vendors Roadmap](BEAT_ALL_VENDORS_ROADMAP.md) — Full backlog and next actions.
- [Fastest at Billing](billing/FASTEST_AT_BILLING.md) — Billing speed criteria, automation, and metrics.
- [EPCR, NEMSIS & Vendor Parity](founder/EPCR_NEMSIS_AND_VENDOR_PARITY.md) — Founder checklist vs ImageTrend, Zoll, ESO, First Due.
- [EMS MDT Competitive Analysis](../EMS_MDT_COMPETITIVE_ANALYSIS.md) — 10 vendors, 13 categories, differentiation opportunities.
- [MDT Competitive Comparison](../mdt-pwa/COMPETITIVE_COMPARISON.md) — MDT feature matrix and gaps.
- [BAA & Breach](compliance/BAA_AND_BREACH.md) — Vendor BAAs (Metriport, etc.).
- [Comprehensive Gap Analysis](../COMPREHENSIVE_GAP_ANALYSIS.md) — Maturity, competitive gaps.

---

*Last updated: January 2026. Revisit when adding new product lines or changing stack (OCR, Metriport).*
