import uuid
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class UserRole(str, Enum):
    founder = "founder"
    admin = "admin"
    ADMIN = "admin"
    ops_admin = "ops_admin"
    OPS_ADMIN = "ops_admin"
    dispatcher = "dispatcher"
    DISPATCHER = "dispatcher"
    provider = "provider"
    PROVIDER = "provider"
    investor = "investor"
    INVESTOR = "investor"
    founder = "founder"
    FOUNDER = "founder"
    support = "support"
    SUPPORT = "support"
    pilot = "pilot"
    PILOT = "pilot"
    flight_nurse = "flight_nurse"
    FLIGHT_NURSE = "flight_nurse"
    flight_medic = "flight_medic"
    FLIGHT_MEDIC = "flight_medic"
    hems_supervisor = "hems_supervisor"
    HEMS_SUPERVISOR = "hems_supervisor"
    aviation_qa = "aviation_qa"
    AVIATION_QA = "aviation_qa"
    medical_director = "medical_director"
    MEDICAL_DIRECTOR = "medical_director"
    crew = "crew"
    CREW = "crew"
    billing = "billing"
    BILLING = "billing"
    facility_admin = "facility_admin"
    FACILITY_ADMIN = "facility_admin"
    facility_user = "facility_user"
    FACILITY_USER = "facility_user"
    fleet_admin = "fleet_admin"
    FLEET_ADMIN = "fleet_admin"
    fleet_manager = "fleet_manager"
    FLEET_MANAGER = "fleet_manager"
    fleet_supervisor = "fleet_supervisor"
    FLEET_SUPERVISOR = "fleet_supervisor"
    fleet_mechanic = "fleet_mechanic"
    FLEET_MECHANIC = "fleet_mechanic"
    fleet_technician = "fleet_technician"
    FLEET_TECHNICIAN = "fleet_technician"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column("passwordHash", String, nullable=False)
    role = Column(String, default=UserRole.crew.value)
    created_at = Column("createdAt", DateTime(timezone=True), server_default=func.now())
