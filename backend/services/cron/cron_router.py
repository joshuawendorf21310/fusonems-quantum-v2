"""Cron endpoints: call with X-Cron-Secret header for scheduled jobs (no session)."""

import logging
from fastapi import APIRouter, Depends, Header, HTTPException, status

from core.config import settings
from core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cron", tags=["Cron"])


def _require_cron_secret(x_cron_secret: str | None = Header(None, alias="X-Cron-Secret")):
    """Generic cron secret validator - checks ACCOUNT_LIFECYCLE_CRON_SECRET or falls back to NEMSIS_WATCH_CRON_SECRET"""
    secret = getattr(settings, "ACCOUNT_LIFECYCLE_CRON_SECRET", None) or getattr(settings, "NEMSIS_WATCH_CRON_SECRET", None)
    if not secret:
        raise HTTPException(status_code=501, detail="Cron secret not configured (set ACCOUNT_LIFECYCLE_CRON_SECRET or NEMSIS_WATCH_CRON_SECRET)")
    if x_cron_secret != secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid cron secret")


def _require_nemsis_watch_secret(x_cron_secret: str | None = Header(None, alias="X-Cron-Secret")):
    secret = getattr(settings, "NEMSIS_WATCH_CRON_SECRET", None)
    if not secret:
        raise HTTPException(status_code=501, detail="NEMSIS_WATCH_CRON_SECRET not configured")
    if x_cron_secret != secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid cron secret")


@router.post("/nemsis-watch")
def cron_nemsis_watch(
    db: Session = Depends(get_db),
    _: None = Depends(_require_nemsis_watch_secret),
):
    """
    Check for NEMSIS version update. Call periodically (e.g. daily) with:
    curl -X POST -H "X-Cron-Secret: YOUR_SECRET" https://your-api/api/cron/nemsis-watch
    Set NEMSIS_WATCH_CRON_SECRET in .env.
    """
    from services.founder.nemsis_watch_service import check_nemsis_version
    return check_nemsis_version(db)


@router.post("/account-lifecycle")
def cron_account_lifecycle(
    db: Session = Depends(get_db),
    _: None = Depends(_require_cron_secret),
):
    """
    Account lifecycle management job (FedRAMP AC-2(2), AC-2(3)).
    Call daily with:
    curl -X POST -H "X-Cron-Secret: YOUR_SECRET" https://your-api/api/cron/account-lifecycle
    Set ACCOUNT_LIFECYCLE_CRON_SECRET in .env (or use NEMSIS_WATCH_CRON_SECRET as fallback).
    
    This job:
    - Checks for inactive accounts
    - Sends deactivation warnings (30, 15, 7 days before)
    - Disables accounts after 90 days of inactivity
    - Generates compliance reports
    """
    from jobs.account_lifecycle_job import run_account_lifecycle_check
    return run_account_lifecycle_check()
