from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from core.database import Base


class UserRole(str, Enum):
    admin = "admin"
    dispatcher = "dispatcher"
    provider = "provider"
    investor = "investor"
    founder = "founder"
    pilot = "pilot"
    flight_nurse = "flight_nurse"
    flight_medic = "flight_medic"
    hems_supervisor = "hems_supervisor"
    aviation_qa = "aviation_qa"
    medical_director = "medical_director"
    billing = "billing"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True, default="")
    role = Column(String, default=UserRole.dispatcher.value)
    training_mode = Column(Boolean, default=False)
    auth_provider = Column(String, default="local")
    oidc_sub = Column(String, default="", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
