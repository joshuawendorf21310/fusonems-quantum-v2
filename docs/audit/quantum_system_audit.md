# Quantum System Static Audit

Status: Static code audit (no runtime verification). Tests not executed here.

## Scope
- Backend services, models, utilities, config, auth/RBAC, event bus, audit logging, tenant scoping
- Frontend routes, modules, navigation, access gating, error handling
- Integrations: Telnyx, Postmark, Stripe, Office Ally, Lob
- Smart Mode deterministic reasoning + DecisionPacket

## Systems Inventory (Backend)
APIRouter services detected:
- Analytics, Builders, System, Workflows, Legal Portal, Time
- Investor Demo, Medication, AI Console, Lob Webhook
- Fire, Communications (+ webhooks), Compliance
- Documents (Document Studio + Quantum Documents)
- Training Center, Business Ops, QA, Validation
- ePCR, HEMS, Search, Training
- CAD (+ Tracking), Billing (+ Stripe)
- Inventory, Consent, Mail
- Schedule, Narcotics, Jobs, Export, Automation, Repair
- Events, Auth (device + OIDC + local), Founder, Founder Ops
- Patient Portal, Feature Flags, Fleet, Telehealth, Email

Models detected across domains include: CAD, ePCR, Billing, HEMS, Fire, Inventory, Narcotics, Training, QA, Legal, Communications, Documents, Email, Feature Flags, Event Log, Audit Log, Module Registry, Consent, Workflow, Analytics, Jobs, Founders/Investor metrics.

## Frontend Route Coverage (High-Level)
- Landing/auth: `/`, `/login`, `/register`
- Core dashboards: `/dashboard`, `/founder`, `/investor`
- Domain modules: CAD, ePCR, Billing, Comms, Email, Scheduling, Fire, HEMS, Telehealth, Inventory, Narcotics, Fleet, Training, QA, Legal, Search, Analytics, Feature Flags, Builders, Documents, Export/Repair/Jobs

## Core Platform Guarantees (Static)
- Multi-tenant scoping helpers: `backend/utils/tenancy.py`
- Audit logging: `backend/utils/audit.py`, `backend/models/compliance.py`
- Canonical event bus: `backend/utils/events.py`, `backend/models/event.py`
- Legal holds: `backend/utils/legal.py`, `backend/models/legal.py`
- DecisionPacket reasoning: `backend/utils/decision.py`
- Smart Mode flag: `backend/core/config.py`, surfaced via `/api/system/health` and `/api/auth/me`
- Training mode: middleware + request state usage in multiple routers

## Module-by-Module Static Status
PASS means routes + models + UI entry points exist and are wired. PARTIAL means one side present or stubs. FAIL means missing.

- CAD: PASS (routers + models + UI)
- MDT/CrewLink: PASS (tracking endpoints + org-scoped telemetry)
- ePCR: PASS (router + models + UI)
- Billing: PASS (router + models + UI + Stripe)
- Communications: PASS (Telnyx + UI)
- Email Inbox: PASS (Postmark + UI)
- Scheduling: PASS
- Inventory: PASS
- Narcotics: PASS
- Medication: PASS
- Fleet: PASS
- Fire: PASS
- HEMS: PASS
- Telehealth: PASS
- QA / Clinical Review: PASS
- Legal / Discovery: PASS
- Documents (Drive/Vault/Studio): PASS
- Builders: PASS
- Analytics: PASS
- Search / Discovery: PASS
- Exports / Repair: PASS
- Founder / Investor: PASS
- System health / upgrade checks: PASS

## Smart Mode / Deterministic Intelligence
- DecisionPacket generated for OCR, billing readiness, docs retention/hold, comms transcripts.
- AI orchestrator exists for explain-only output (`backend/utils/ai_orchestrator.py`).
- No direct OpenAI usage found.

## Security / RBAC (Static)
- Backend role guards in routers using `require_roles`, `require_module`.
- UI gating uses `canAccessModule` + module registry flags.
- CSRF middleware for cookie auth; webhooks exempted.

## Integrations
- Telnyx: inbound webhooks + comms module, signature verification.
- Postmark: inbound + outbound transport, signature verification.
- Stripe: billing webhooks + setup script.
- Lob: webhook endpoint present.
- Office Ally: FTP config present; export modules present.

## Findings (Static)
- `backend/models/mail.py` + `backend/services/mail/mail_router.py` still exist alongside Postmark email system. This is legacy and can cause confusion. Recommend deprecate or align with Postmark-only transport.
- Frontend uses system guidance panels but lacks explicit drill-down for email DecisionPacket explanations; currently only text hints.
- Thread preview uses full message fetch; consider adding lightweight server endpoint for performance at scale.

## Tests
- Test suite present across modules.
- Unable to run tests in this environment (pytest not installed). Runtime verification pending.

## Verdict
Static audit: PASS with noted limitations. Runtime audit pending test execution.
