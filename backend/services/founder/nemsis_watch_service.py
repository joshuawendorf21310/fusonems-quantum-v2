"""
NEMSIS version watch: check nemsis.org (or NEMSIS_VERSION_CHECK_URL) for current
NEMSIS version and notify founders when a new version is detected.
"""

import logging
import re
from typing import Any, Dict, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from core.config import settings
from models.nemsis_watch import NemsisVersionWatch
from models.notifications import InAppNotification, NotificationSeverity, NotificationType
from models.user import User, UserRole

logger = logging.getLogger(__name__)

# Default URL to check for version text (NEMSIS v3.5 resources page)
DEFAULT_VERSION_CHECK_URL = "https://nemsis.org/v3-5-revision/v3-5-resources/"
VERSION_PATTERN = re.compile(r"3\.(\d+)\.(\d+)")


def _parse_version_from_text(text: str) -> Optional[str]:
    """Extract highest 3.x.y version from page content."""
    matches = VERSION_PATTERN.findall(text)
    if not matches:
        return None
    # Take highest minor.patch for major 3
    best = None
    for minor, patch in matches:
        v = f"3.{minor}.{patch}"
        if best is None or (int(minor), int(patch)) > (int(best.split(".")[1]), int(best.split(".")[2])):
            try:
                best = v
            except (ValueError, IndexError):
                pass
    return best


def fetch_current_nemsis_version() -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch current NEMSIS version from configured URL or default.
    Returns (version_string or None, error_message or None).
    """
    url = getattr(settings, "NEMSIS_VERSION_CHECK_URL", None) or DEFAULT_VERSION_CHECK_URL
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            text = r.text
    except Exception as e:
        logger.warning("NEMSIS version check fetch failed: %s", e)
        return None, str(e)
    version = _parse_version_from_text(text)
    return version, None


def _version_tuple(v: str) -> Tuple[int, int, int]:
    try:
        parts = v.strip().split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    except (ValueError, IndexError):
        return (0, 0, 0)


def is_newer_version(current: str, known: str) -> bool:
    """Return True if current > known (e.g. 3.5.2 > 3.5.1)."""
    return _version_tuple(current) > _version_tuple(known)


def get_or_create_watch_row(db: Session) -> NemsisVersionWatch:
    row = db.query(NemsisVersionWatch).filter(NemsisVersionWatch.id == 1).first()
    if not row:
        row = NemsisVersionWatch(id=1, last_known_version="3.5.1")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def check_nemsis_version(db: Session) -> Dict[str, Any]:
    """
    Check for NEMSIS version update. Fetches current version, compares to
    last_known in DB; if newer, notifies founders and updates last_notified.
    Returns dict with: current_version, last_known, updated (bool), notified (bool), error.
    """
    from datetime import datetime, timezone

    row = get_or_create_watch_row(db)
    current_version, err = fetch_current_nemsis_version()
    now = datetime.now(timezone.utc)
    row.last_checked_at = now
    db.commit()

    if err or not current_version:
        return {
            "current_version": current_version,
            "last_known_version": row.last_known_version,
            "updated": False,
            "notified": False,
            "error": err or "No version parsed from page",
        }

    updated = is_newer_version(current_version, row.last_known_version)
    if updated:
        row.last_known_version = current_version
        db.commit()
        db.refresh(row)

    # Notify founders if we haven't already notified for this version
    notified = False
    if updated and (row.last_notified_version is None or is_newer_version(current_version, row.last_notified_version)):
        notified = notify_founders_nemsis_update(db, current_version)
        if notified:
            row.last_notified_version = current_version
            db.commit()

    return {
        "current_version": current_version,
        "last_known_version": row.last_known_version,
        "updated": updated,
        "notified": notified,
        "error": None,
    }


def notify_founders_nemsis_update(db: Session, new_version: str) -> bool:
    """Create in-app notifications and send email to founders for NEMSIS update. Returns True if any notification sent."""
    # Limit queries to prevent performance issues - typically only a few founders/admins exist
    founders = db.query(User).filter(User.role == UserRole.founder).limit(100).all()
    admins = db.query(User).filter(User.role == UserRole.admin).limit(100).all()
    # Notify founders first; optionally include first admin per org
    users_to_notify = list(founders)
    if not users_to_notify:
        users_to_notify = list(admins[:5])
    if not users_to_notify:
        logger.info("No founder or admin users to notify for NEMSIS update")
        return False

    title = "NEMSIS standard update available"
    body = f"NEMSIS version {new_version} has been detected. Review nemsis.org for Schematron and dataset updates and plan platform compliance."

    from services.notifications.notification_dispatcher import NotificationDispatcher
    from services.email.email_transport_service import send_notification_email

    for user in users_to_notify:
        try:
            notif = NotificationDispatcher.dispatch_notification(
                db,
                user_id=user.id,
                org_id=user.org_id,
                notification_type=NotificationType.NEMSIS_UPDATE,
                title=title,
                body=body,
                severity=NotificationSeverity.WARNING,
                linked_resource_type="compliance",
                metadata={"nemsis_version": new_version},
            )
            if notif:
                logger.info("NEMSIS update notification sent to user %s", user.id)
        except Exception as e:
            logger.exception("Failed to dispatch NEMSIS update notification to user %s: %s", user.id, e)

    # Email to FOUNDER_EMAIL (one email for all)
    to = getattr(settings, "FOUNDER_EMAIL", None) or (users_to_notify[0].email if users_to_notify else None)
    if to:
        try:
            send_notification_email(
                to=to,
                subject=title,
                html_body=f"<p>{body}</p><p>Check the Founder dashboard for compliance and Schematron updates.</p>",
            )
            logger.info("NEMSIS update email sent to %s", to)
        except Exception as e:
            logger.exception("Failed to send NEMSIS update email: %s", e)

    return True
