"""
Founder AI Assistant: ChatGPT-like assistant for fix, add, enhance, suggest, and self-heal.
Gathers platform context (queue, health, failed ops, audits) and uses Ollama to reply.
When allow_self_heal is True, runs safe automated actions (retry failed jobs, NEMSIS check).
"""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from clients.ollama_client import OllamaClient
from core.config import settings
from models.compliance import ForensicAuditLog
from models.jobs import JobQueue
from services.founder.system_health_service import SystemHealthService
from utils.logger import logger


def _queue_summary(db: Session, org_id: int) -> Dict[str, Any]:
    base = db.query(JobQueue).filter(JobQueue.org_id == org_id)
    total = base.count()
    pending = base.filter(JobQueue.status == "queued").count()
    with_errors = base.filter(JobQueue.last_error != "").count()
    error_rate = round(with_errors / total, 3) if total else 0.0
    return {
        "total": total,
        "queued": pending,
        "errors": with_errors,
        "error_rate": error_rate,
    }


def _failed_jobs(db: Session, org_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    rows = (
        db.query(JobQueue)
        .filter(JobQueue.org_id == org_id, JobQueue.last_error != "")
        .order_by(JobQueue.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "job_type": r.job_type,
            "status": r.status,
            "last_error": (r.last_error or "")[:500],
            "attempts": r.attempts,
        }
        for r in rows
    ]


def _critical_audits(db: Session, org_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    filter_expr = or_(
        ForensicAuditLog.action.ilike("%auth%"),
        ForensicAuditLog.resource.ilike("%billing%"),
        ForensicAuditLog.resource.ilike("%merge%"),
        ForensicAuditLog.action.ilike("%merge%"),
        ForensicAuditLog.action.ilike("%lock%"),
        ForensicAuditLog.action.ilike("%export%"),
    )
    records = (
        db.query(ForensicAuditLog)
        .filter(ForensicAuditLog.org_id == org_id)
        .filter(filter_expr)
        .order_by(ForensicAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": record.id,
            "actor_email": record.actor_email,
            "action": record.action,
            "resource": record.resource,
            "outcome": record.outcome,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        for record in records
    ]


def get_context(db: Session, org_id: int) -> Dict[str, Any]:
    """Build context for the AI: queue, system health, failed jobs, recent critical audits."""
    queue = _queue_summary(db, org_id)
    failed_jobs = _failed_jobs(db, org_id)
    audits = _critical_audits(db, org_id)
    try:
        health = SystemHealthService.get_unified_system_health(db, org_id)
    except Exception as e:
        logger.warning(f"AI assistant context: system health failed: {e}")
        health = {
            "overall_status": "UNKNOWN",
            "overall_message": str(e),
            "critical_issues": [],
            "warnings": [],
        }
    return {
        "queue_summary": queue,
        "failed_jobs": failed_jobs,
        "critical_audits_sample": audits,
        "system_health": {
            "overall_status": health.get("overall_status", "UNKNOWN"),
            "overall_message": health.get("overall_message", ""),
            "critical_issues": health.get("critical_issues", [])[:10],
            "warnings": health.get("warnings", [])[:10],
        },
    }


def run_self_heal_actions(db: Session, org_id: int) -> List[Dict[str, Any]]:
    """
    Run safe, automated self-heal actions: retry failed jobs, check NEMSIS version.
    Returns list of { "action": str, "result": str, "detail": optional }.
    """
    actions_taken: List[Dict[str, Any]] = []

    # 1. Reset failed jobs to queued so they can be retried
    failed = (
        db.query(JobQueue)
        .filter(JobQueue.org_id == org_id, JobQueue.last_error != "")
        .all()
    )
    if failed:
        count = 0
        for job in failed:
            job.status = "queued"
            job.last_error = ""
            count += 1
        db.commit()
        actions_taken.append({
            "action": "retry_failed_jobs",
            "result": "success",
            "detail": f"Re-queued {count} job(s) for retry.",
        })
    else:
        actions_taken.append({
            "action": "retry_failed_jobs",
            "result": "skipped",
            "detail": "No failed jobs to retry.",
        })

    # 2. NEMSIS version check (notify if update available)
    try:
        from services.founder.nemsis_watch_service import check_nemsis_version
        nemsis_result = check_nemsis_version(db)
        notified = nemsis_result.get("notified") or False
        current = nemsis_result.get("current_version") or nemsis_result.get("last_known_version") or "unknown"
        actions_taken.append({
            "action": "nemsis_version_check",
            "result": "success",
            "detail": f"Checked NEMSIS version ({current}). Notified: {notified}.",
        })
    except Exception as e:
        logger.warning(f"AI assistant self-heal: NEMSIS check failed: {e}")
        actions_taken.append({
            "action": "nemsis_version_check",
            "result": "error",
            "detail": str(e),
        })

    return actions_taken


SYSTEM_PROMPT = """You are the FusionEMS Quantum Founder Assistant. You help founders and ops admins:
- **Fix** things: diagnose queue errors, health issues, failed jobs, and suggest or confirm fixes.
- **Add** things: suggest new features, integrations, or configuration based on platform context.
- **Enhance** things: recommend improvements to workflows, compliance, terminology, or builder systems.
- **Suggest** things: proactive suggestions from queue summary, system health, and recent audits.

You have access to live context: queue summary (total, queued, errors), failed jobs list, system health (overall status, critical issues, warnings), and a sample of recent critical audits. Use this context to give specific, actionable answers. If the user enables "self-healing", safe automated actions (e.g. re-queue failed jobs, NEMSIS version check) may already have been run; summarize what was done and any follow-up they should take. Be concise but complete. Answer in markdown when helpful (lists, bold)."""


def build_messages(
    user_message: str,
    context: Dict[str, Any],
    actions_taken: Optional[List[Dict[str, Any]]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, str]]:
    """Build Ollama chat messages: system context + optional history + latest user turn + place for assistant."""
    context_blob = json.dumps(context, indent=2)
    intro = "Current platform context (use this to answer):\n```json\n" + context_blob + "\n```\n"
    if actions_taken:
        intro += "\nSelf-heal actions just run:\n" + json.dumps(actions_taken, indent=2) + "\n"
    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + intro}]

    if history:
        for h in history[-10:]:  # last 10 turns
            role = h.get("role")
            content = h.get("content") or ""
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})
    return messages


async def chat(
    db: Session,
    org_id: int,
    user_message: str,
    allow_self_heal: bool = False,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Run AI assistant turn: gather context, optionally run self-heal, call Ollama, return reply + actions_taken.
    """
    context = get_context(db, org_id)
    actions_taken: List[Dict[str, Any]] = []

    if allow_self_heal:
        actions_taken = run_self_heal_actions(db, org_id)
        # Refresh context after self-heal so reply reflects new state
        context = get_context(db, org_id)

    model = getattr(settings, "OLLAMA_IVR_MODEL", "llama3.2") or "llama3.2"
    client = OllamaClient()

    messages = build_messages(user_message, context, actions_taken if actions_taken else None, history)
    try:
        response = await client.chat(messages=messages, model=model)
    except Exception as e:
        logger.exception("AI assistant Ollama chat failed")
        return {
            "reply": f"I couldn't reach the AI service: {e}. Check that Ollama is running and {getattr(settings, 'OLLAMA_SERVER_URL', '')} is correct.",
            "actions_taken": actions_taken,
        }

    reply = ""
    if isinstance(response, dict):
        msg = response.get("message") or response.get("message")
        if isinstance(msg, dict):
            reply = (msg.get("content") or "").strip()
        elif isinstance(msg, str):
            reply = msg.strip()
        if not reply and response.get("error"):
            reply = f"AI error: {response['error']}"

    if not reply:
        reply = "I didn't get a response from the model. Try again or check Ollama."

    return {"reply": reply, "actions_taken": actions_taken}
