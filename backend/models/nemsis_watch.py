"""NEMSIS version watch: track last known NEMSIS version and notify on updates."""

from sqlalchemy import Column, DateTime, Integer, String, func
from core.database import Base


class NemsisVersionWatch(Base):
    """Single-row table: last known NEMSIS version and last notified version for update alerts."""
    __tablename__ = "nemsis_version_watch"

    id = Column(Integer, primary_key=True, index=True, default=1)
    last_known_version = Column(String(32), default="3.5.1", nullable=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_notified_version = Column(String(32), nullable=True)  # last version we sent notification for
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
