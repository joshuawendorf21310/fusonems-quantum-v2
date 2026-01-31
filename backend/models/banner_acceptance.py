"""
Banner Acceptance Model for FedRAMP AC-8 Compliance

Tracks user acceptance of system use notification banner.
FedRAMP AC-8 requires:
- Display system use notification before granting access
- Track user acceptance with timestamp, IP, and banner version
- Retain consent records for compliance
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func, Index
from sqlalchemy.orm import relationship

from core.database import Base


class BannerAcceptance(Base):
    """
    Tracks user acceptance of system use notification banner.
    
    FedRAMP AC-8 requires:
    - System use notification displayed before access
    - User acceptance tracked with timestamp
    - IP address recorded
    - Banner version tracked for compliance
    """
    __tablename__ = "banner_acceptances"
    __table_args__ = (
        # Index for checking if user has accepted current banner version
        Index('idx_banner_user_version', 'user_id', 'banner_version'),
        # Index for compliance reporting
        Index('idx_banner_acceptance_date', 'accepted_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    banner_version = Column(String(50), nullable=False, index=True)  # Version identifier for banner text
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String, nullable=True)  # User agent string
    accepted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationship
    user = relationship("User", backref="banner_acceptances")

    def __repr__(self):
        return (
            f"<BannerAcceptance(id={self.id}, "
            f"user_id={self.user_id}, "
            f"banner_version={self.banner_version}, "
            f"accepted_at={self.accepted_at})>"
        )
