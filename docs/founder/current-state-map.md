# FusionEMS Quantum: Current State Map

## Backend APIs (Documents / Legal Hold / Comms)
- Documents (Document Studio):
  - `backend/services/documents/document_router.py`
    - `/api/documents/templates` (GET/POST)
    - `/api/documents/templates/{template_id}/activate` (POST)
    - `/api/documents/records` (GET/POST)
- Legal Hold / Addenda / Overrides:
  - `backend/services/legal/legal_router.py`
    - `/api/legal-hold` (POST/GET)
    - `/api/legal-hold/{hold_id}/release` (POST)
    - `/api/legal-hold/addenda` (POST/GET)
    - `/api/legal-hold/overrides` (POST)
    - `/api/legal-hold/overrides/{override_id}/approve` (POST)
- Legal Portal:
  - `backend/services/legal_portal/legal_portal_router.py`
    - `/api/legal-portal/*` (case/evidence management)
- Communications (Telnyx):
  - `backend/services/communications/comms_router.py`
    - `/api/comms/*` (threads, messages, calls)
    - `/api/comms/webhooks/telnyx` (webhook intake)

## Telnyx Config / Env Vars
- Config:
  - `backend/core/config.py` (TELNYX_API_KEY, TELNYX_NUMBER, TELNYX_CONNECTION_ID, TELNYX_MESSAGING_PROFILE_ID,
    TELNYX_PUBLIC_KEY, TELNYX_REQUIRE_SIGNATURE)
- Environment Example:
  - `backend/.env.example` (TELNYX_* keys)

## Audit / Event Writers
- Audit:
  - `backend/utils/audit.py` (record_audit)
  - `backend/utils/tenancy.py` (org scoping audit)
- Canonical Events:
  - `backend/utils/events.py` (event bus)
  - `backend/utils/write_ops.py` (audit_and_event)
  - `backend/services/events/event_router.py` (publish/replay endpoints)
  - `backend/services/events/event_handlers.py` (event handlers)

## Frontend Pages / Components (Docs, Comms, Legal, Founder)
- Document Studio:
  - `next-fusionems/src/pages/DocumentStudio.jsx`
  - `next-fusionems/src/components/Sidebar.jsx` (nav entry `/documents`)
- Communications:
  - `next-fusionems/src/pages/Communications.jsx`
  - `next-fusionems/src/pages/modules/Communications.jsx`
  - `next-fusionems/src/components/Sidebar.jsx` (nav entry `/communications`)
- Legal:
  - `next-fusionems/src/pages/LegalPortal.jsx`
  - `next-fusionems/src/pages/HemsQA.jsx` (legal hold visibility)
  - `next-fusionems/src/components/LegalHoldBanner.jsx`
  - `next-fusionems/src/components/Sidebar.jsx` (nav entry `/legal-portal`)
- Founder:
  - `next-fusionems/src/pages/FounderDashboard.jsx`
  - `next-fusionems/src/pages/FounderOps.jsx`
  - `next-fusionems/src/components/Sidebar.jsx` (nav entry `/founder`, `/founder-ops`)
