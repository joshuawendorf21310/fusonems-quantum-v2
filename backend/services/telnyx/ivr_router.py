from __future__ import annotations

import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.params import Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.organization import Organization
from core.guards import require_module
from core.security import require_roles
from models.telnyx import TelnyxCallSummary
from models.user import User, UserRole
from services.telnyx.helpers import (
    get_system_user,
    module_enabled,
    require_telnyx_enabled,
    resolve_org,
    verify_telnyx_signature,
)
from services.telnyx.telnyx_service import TelnyxFaxHandler, TelnyxIVRService


router = APIRouter(prefix="/api/telnyx", tags=["Telnyx"])


def _texml(s: str) -> Response:
    return Response(content=s, media_type="application/xml")


def _base_url() -> str:
    base = (settings.APP_BASE_URL or "").rstrip("/")
    if not base:
        base = "https://your-backend.example.com"
    return base


class CallSummaryRequest(BaseModel):
    call_sid: str
    intent: str
    transcript: dict[str, Any] = {}
    ai_response: dict[str, Any] = {}
    resolution: str | None = None
    reason: str | None = None


def _ensure_module(org_id: int, db: Session) -> None:
    if not module_enabled(db, org_id):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MODULE_DISABLED:BILLING")


@router.post("/incoming-call")
async def incoming_call(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    require_telnyx_enabled()
    raw_body = await request.body()
    verify_telnyx_signature(raw_body, request)
    data = json.loads(raw_body.decode("utf-8") or "{}")
    payload = data.get("data", {}).get("payload") or data.get("payload") or {}
    org = resolve_org(db, payload)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="org_not_found")
    _ensure_module(org.id, db)
    user = get_system_user(db, org.id)
    service = TelnyxIVRService(db, org.id)
    result = service.handle_incoming_call(request, user, payload)
    return {"detail": "call_processed", "result": result}


@router.post("/call-summary")
def post_call_summary(
    payload: CallSummaryRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    require_telnyx_enabled()
    _ensure_module(user.org_id, db)
    service = TelnyxIVRService(db, user.org_id)
    record = service.record_call_summary(
        request,
        user,
        payload.dict(),
        payload.ai_response,
        payload.intent,
        payload.reason or "manual",
        resolution=payload.resolution,
    )
    return {"summary_id": record.id, "status": record.resolution}


@router.get("/call-history")
def call_history(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    require_telnyx_enabled()
    _ensure_module(user.org_id, db)
    query = (
        db.query(TelnyxCallSummary)
        .filter(TelnyxCallSummary.org_id == user.org_id)
        .order_by(TelnyxCallSummary.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    summaries = query.all()
    return {
        "summaries": [
            {
                "id": summary.id,
                "intent": summary.intent,
                "ai_model": summary.ai_model,
                "resolution": summary.resolution,
                "created_at": summary.created_at.isoformat() if summary.created_at else None,
            }
            for summary in summaries
        ]
    }


@router.post("/fax-received")
async def fax_received(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    require_telnyx_enabled()
    raw_body = await request.body()
    verify_telnyx_signature(raw_body, request)
    data = json.loads(raw_body.decode("utf-8") or "{}")
    payload = data.get("data", {}).get("payload") or data.get("payload") or {}
    org = resolve_org(db, payload)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="org_not_found")
    _ensure_module(org.id, db)
    user = get_system_user(db, org.id)
    fax_handler = TelnyxFaxHandler(db, org.id)
    record = fax_handler.store_fax(request, user, payload)
    return {"detail": "fax_processed", "fax_id": record.id}


# ---------- IVR TeXML: dial 1 for billing, 2 for payment, 3 for agent ----------

@router.get("/texml/welcome")
def texml_welcome() -> Response:
    """Returns TeXML: greeting + 'Press 1 for billing, 2 for payment, 3 for representative' + Gather."""
    require_telnyx_enabled()
    menu = TelnyxIVRService.IVR_MENU_TEXT
    base = _base_url()
    action_url = f"{base}/api/telnyx/texml/choice"
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="female">{_escape_xml(menu)}</Say>
  <Gather numDigits="1" action="{_escape_xml(action_url)}" method="POST" timeout="5"/>
  <Say voice="female">We didn't receive a selection. Goodbye.</Say>
  <Hangup/>
</Response>"""
    return _texml(xml)


@router.get("/texml/choice")
def texml_choice_get(
    digits: str = Query("", alias="digits"),
    db: Session = Depends(get_db),
) -> Response:
    """After IVR digit: 1/2 = Ollama AI biller helper (human-like), 3 = transfer to agent."""
    require_telnyx_enabled()
    digit = (digits or "").strip()[:1]
    return _texml_choice_response(digit, db)


@router.post("/texml/choice")
async def texml_choice_post(request: Request, db: Session = Depends(get_db)) -> Response:
    """Same as GET; Telnyx may POST digits in form body."""
    require_telnyx_enabled()
    try:
        form = await request.form()
        digits = form.get("digits") or form.get("Digits") or ""
    except Exception:
        digits = ""
    if not digits:
        digits = request.query_params.get("digits") or ""
    digit = (str(digits).strip())[:1]
    return _texml_choice_response(digit, db)


def _texml_choice_response(digit: str, db: Session) -> Response:
    """Build TeXML response for IVR choice (1/2 = AI biller, 3 = transfer)."""
    base = _base_url()
    welcome_url = f"{base}/api/telnyx/texml/welcome"

    if digit == "3":
        transfer = getattr(settings, "TELNYX_TRANSFER_NUMBER", None) or settings.TELNYX_FROM_NUMBER
        if transfer:
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="female">Connecting you with a representative now.</Say>
  <Dial><Number>{_escape_xml(transfer)}</Number></Dial>
  <Say voice="female">The call could not be completed. Please try again later.</Say>
  <Hangup/>
</Response>"""
        else:
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="female">Representatives are not available at this moment. Please call back or leave a message.</Say>
  <Hangup/>
</Response>"""
        return _texml(xml)

    if digit in ("1", "2"):
        intent = "billing_questions" if digit == "1" else "payment_status"
        org = db.query(Organization).order_by(Organization.id.asc()).first()
        if org:
            service = TelnyxIVRService(db, org.id)
            result = service.route_to_ai_biller_helper("", intent)
            text = (result.get("response") or "I can help with that. What would you like to know?").strip()
            if len(text) > 500:
                text = text[:497] + "..."
            text = _escape_xml(text)
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="female">{text}</Say>
  <Say voice="female">If you need more help, press 3 to speak with someone. Otherwise, thank you for calling. Goodbye.</Say>
  <Hangup/>
</Response>"""
        else:
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="female">Our billing assistant can help with that. What's your question? You can also press 3 to speak with a representative.</Say>
  <Hangup/>
</Response>"""
        return _texml(xml)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="female">Sorry, that wasn't a valid option. Let me try again.</Say>
  <Redirect>{_escape_xml(welcome_url)}</Redirect>
</Response>"""
    return _texml(xml)


def _escape_xml(s: str) -> str:
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
