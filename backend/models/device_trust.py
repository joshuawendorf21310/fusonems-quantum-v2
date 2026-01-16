from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from core.database import Base


class DeviceTrust(Base):
    __tablename__ = "device_trust"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    fingerprint = Column(String, default="")
    trusted = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
