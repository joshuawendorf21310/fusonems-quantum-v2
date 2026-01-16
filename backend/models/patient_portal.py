from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class PatientPortalAccount(Base):
    __tablename__ = "patient_portal_accounts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    patient_name = Column(String, nullable=False)
    email = Column(String, default="")
    status = Column(String, default="active")
    preferences = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PatientPortalMessage(Base):
    __tablename__ = "patient_portal_messages"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("patient_portal_accounts.id"), nullable=False)
    sender = Column(String, default="patient")
    message = Column(String, nullable=False)
    status = Column(String, default="new")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
