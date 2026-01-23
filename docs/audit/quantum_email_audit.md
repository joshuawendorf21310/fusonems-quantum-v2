# Quantum Email Audit

Status: Drafted after implementation review. Tests not executed in this environment.

## Scope
- Postmark transport integration
- Inbound webhook ingestion
- Internal threading + labels
- Document attachment handling
- Retention + legal hold enforcement
- Audit + canonical events
- Inbox UI (Gmail-style command surface)

## Route Inventory
- POST `/api/email/inbound/postmark`
- POST `/api/email/send`
- GET `/api/email/threads`
- GET `/api/email/threads/{thread_id}`
- GET `/api/email/messages`
- GET `/api/email/messages/{message_id}/attachments`
- GET `/api/email/labels`
- POST `/api/email/messages/{message_id}/labels`
- POST `/api/email/messages/{message_id}/archive`
- DELETE `/api/email/messages/{message_id}`
- GET `/api/email/search`

## Storage + Attachment Handling
- Attachments stored in Quantum Documents storage via `build_storage_key`.
- Email links to document IDs only via `EmailAttachmentLink`.

## Retention + Legal Hold
- Delete attempts produce DecisionPacket and block when hold/retention active.
- Rule IDs: `EMAIL.RETENTION.BLOCK_DELETE.v1`, `EMAIL.LEGAL_HOLD.BLOCK.v1`.

## Audit + Events
- Inbound receive emits audit/event via `email_ingest_service`.
- Outbound send emits audit/event via `email_transport_service`.
- Label changes + archive emit audit/event via `email_router`.

## Postmark Verification
- Signature verification via `X-Postmark-Signature` enforced when enabled.

## UI / UX
- 3-pane Gmail-style layout: labels (left), threads (center), context (right).
- Search-first workflow with quick filters and match reasons.
- Always-alive guidance panels and action bar.

## PASS / FAIL Table
| Requirement | Status | Evidence |
| --- | --- | --- |
| Postmark inbound webhook | PASS | `backend/services/email/email_router.py` |
| Postmark signature verification | PASS | `backend/services/email/email_ingest_service.py` |
| Outbound send via transport service | PASS | `backend/services/email/email_transport_service.py` |
| Internal threading | PASS | `backend/models/email.py` + `email_ingest_service` |
| Deterministic labels | PASS | `email_ingest_service._apply_labels` |
| Attachments stored in Documents | PASS | `email_ingest_service` + `EmailAttachmentLink` |
| Retention + legal hold blocks | PASS | `backend/services/email/email_router.py` |
| Audit + events for actions | PASS | `email_router`, `email_ingest_service`, `email_transport_service` |
| Search criteria support | PASS | `email_router.search_messages` |
| UI Gmail-style layout | PASS | `next-fusionems/src/pages/EmailInbox.jsx`, `next-fusionems/src/style.css` |
| Tests present | PASS | `backend/tests/test_email_postmark.py` |
| Tests executed | FAIL | Not run in this environment |

## Known Limitations
- Tests not executed here; run `PYTHONPATH=. pytest -q backend/tests/test_email_postmark.py`.
- UI uses client-side fetch of threads + messages; a server-side thread preview endpoint could reduce payload size.

## Verdict
Implementation complete pending test execution.
