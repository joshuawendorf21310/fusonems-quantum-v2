from sqlalchemy import Column, DateTime, Integer, String, func

from core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    encryption_key = Column(String, nullable=False)
    lifecycle_state = Column(String, default="ACTIVE")
    status = Column(String, default="Active")
    email_domain = Column(String, default="")
    training_mode = Column(String, default="DISABLED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
