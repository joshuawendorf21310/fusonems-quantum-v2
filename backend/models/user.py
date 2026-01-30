from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import synonym

from core.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    OPS_ADMIN = "ops_admin"
    DISPATCHER = "dispatcher"
    PROVIDER = "provider"
    INVESTOR = "investor"
    FOUNDER = "founder"
    SUPPORT = "support"
    PILOT = "pilot"
    FLIGHT_NURSE = "flight_nurse"
    FLIGHT_MEDIC = "flight_medic"
    HEMS_SUPERVISOR = "hems_supervisor"
    AVIATION_QA = "aviation_qa"
    MEDICAL_DIRECTOR = "medical_director"
    CREW = "crew"
    BILLING = "billing"
    FACILITY_ADMIN = "facility_admin"
    FACILITY_USER = "facility_user"
    FLEET_ADMIN = "fleet_admin"
    FLEET_MANAGER = "fleet_manager"
    FLEET_SUPERVISOR = "fleet_supervisor"
    FLEET_MECHANIC = "fleet_mechanic"
    FLEET_TECHNICIAN = "fleet_technician"
    COMPLIANCE = "compliance"
    PATIENT = "patient"

    # lowercase aliases
    compliance = COMPLIANCE
    patient = PATIENT
    founder = FOUNDER
    admin = ADMIN
    ops_admin = OPS_ADMIN
    dispatcher = DISPATCHER
    provider = PROVIDER
    investor = INVESTOR
    support = SUPPORT
    pilot = PILOT
    flight_nurse = FLIGHT_NURSE
    flight_medic = FLIGHT_MEDIC
    hems_supervisor = HEMS_SUPERVISOR
    aviation_qa = AVIATION_QA
    medical_director = MEDICAL_DIRECTOR
    crew = CREW
    billing = BILLING
    facility_admin = FACILITY_ADMIN
    facility_user = FACILITY_USER
    fleet_admin = FLEET_ADMIN
    fleet_manager = FLEET_MANAGER
    fleet_supervisor = FLEET_SUPERVISOR
    fleet_mechanic = FLEET_MECHANIC
    fleet_technician = FLEET_TECHNICIAN


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column("hashed_password", String, nullable=True)
    password_hash = synonym("hashed_password")
    role = Column(String, default=UserRole.crew.value)
    must_change_password = Column(Boolean, default=False, nullable=False)
    created_at = Column("createdAt", DateTime(timezone=True), server_default=func.now())
