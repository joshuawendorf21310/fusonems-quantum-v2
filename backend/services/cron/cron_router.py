"""Cron endpoints: call with X-Cron-Secret header for scheduled jobs (no session)."""

import logging
from fastapi import APIRouter, Depends, Header, HTTPException, status

from core.config import settings
from core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cron", tags=["Cron"])


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
