from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum
from core.database import Base


class InspectionStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FAILED = "failed"
    OVERDUE = "overdue"


class HydrantStatus(str, Enum):
    OPERATIONAL = "operational"
    OUT_OF_SERVICE = "out_of_service"
    NEEDS_REPAIR = "needs_repair"


class FirePersonnel(Base):
    __tablename__ = "fire_personnel"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    
    badge_number = Column(String, unique=True)
    rank = Column(String, nullable=False)
    
    station_assignment = Column(String, nullable=False)
    shift_assignment = Column(String)
    apparatus_assignment = Column(String)
    
    firefighter_certification_level = Column(String)
    driver_operator_certified = Column(Boolean, default=False)
    hazmat_certified = Column(Boolean, default=False)
    technical_rescue_certified = Column(Boolean, default=False)
    
    last_physical_date = Column(Date)
    next_physical_due = Column(Date)
    physical_passed = Column(Boolean)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="OPS")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Hydrant(Base):
    __tablename__ = "hydrants"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    hydrant_number = Column(String, nullable=False, index=True)
    
    address = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    
    hydrant_type = Column(String)
    flow_capacity_gpm = Column(Integer)
    static_pressure_psi = Column(Integer)
    residual_pressure_psi = Column(Integer)
    
    manufacturer = Column(String)
    install_date = Column(Date)
    
    status = Column(SQLEnum(HydrantStatus), default=HydrantStatus.OPERATIONAL)
    
    last_inspection_date = Column(Date)
    next_inspection_due = Column(Date)
    
    last_maintenance_date = Column(Date)
    next_maintenance_due = Column(Date)
    
    notes = Column(Text)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="OPS")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HydrantInspection(Base):
    __tablename__ = "hydrant_inspections"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    hydrant_id = Column(Integer, ForeignKey("hydrants.id"), nullable=False)
    
    inspection_date = Column(Date, nullable=False)
    inspector_id = Column(Integer, ForeignKey("fire_personnel.id"))
    
    flow_test_performed = Column(Boolean, default=False)
    static_pressure_psi = Column(Integer)
    residual_pressure_psi = Column(Integer)
    flow_gpm = Column(Integer)
    
    valve_operational = Column(Boolean, default=True)
    cap_threads_good = Column(Boolean, default=True)
    paint_condition = Column(String)
    
    deficiencies_found = Column(Text)
    repairs_needed = Column(Text)
    
    status = Column(SQLEnum(InspectionStatus), default=InspectionStatus.COMPLETED)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="OPS")
    created_at = Column(DateTime, default=datetime.utcnow)


class FireInspection(Base):
    __tablename__ = "fire_inspections"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    inspection_number = Column(String, nullable=False, index=True)
    
    property_name = Column(String, nullable=False)
    property_address = Column(String, nullable=False)
    property_type = Column(String, nullable=False)
    
    occupancy_type = Column(String)
    occupant_load = Column(Integer)
    
    inspection_date = Column(Date, nullable=False)
    inspector_id = Column(Integer, ForeignKey("fire_personnel.id"))
    
    inspection_type = Column(String, nullable=False)
    
    violations_found = Column(Integer, default=0)
    critical_violations = Column(Integer, default=0)
    
    status = Column(String, default="passed")
    
    sprinkler_system = Column(Boolean, default=False)
    fire_alarm = Column(Boolean, default=False)
    fire_extinguishers = Column(Boolean, default=False)
    emergency_lighting = Column(Boolean, default=False)
    exit_signs = Column(Boolean, default=False)
    
    violations_description = Column(Text)
    corrective_actions_required = Column(Text)
    
    re_inspection_required = Column(Boolean, default=False)
    re_inspection_date = Column(Date)
    
    notes = Column(Text)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="OPS")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PreFirePlan(Base):
    __tablename__ = "pre_fire_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    plan_number = Column(String, nullable=False, index=True)
    
    property_name = Column(String, nullable=False)
    property_address = Column(String, nullable=False)
    
    latitude = Column(Float)
    longitude = Column(Float)
    
    occupancy_type = Column(String, nullable=False)
    occupant_load = Column(Integer)
    
    number_of_floors = Column(Integer)
    square_footage = Column(Integer)
    construction_type = Column(String)
    roof_type = Column(String)
    
    hazardous_materials_present = Column(Boolean, default=False)
    hazmat_types = Column(JSON)
    
    sprinkler_system = Column(Boolean, default=False)
    standpipe_system = Column(Boolean, default=False)
    fire_alarm_type = Column(String)
    
    nearest_hydrant_distance_feet = Column(Integer)
    water_supply_notes = Column(Text)
    
    knox_box_location = Column(String)
    fire_department_connection_location = Column(String)
    
    floor_plan_path = Column(String)
    site_plan_path = Column(String)
    
    property_manager_name = Column(String)
    property_manager_phone = Column(String)
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    
    created_by = Column(String)
    last_updated_by = Column(String)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="OPS")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CommunityRiskReduction(Base):
    __tablename__ = "community_risk_reduction"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    program_name = Column(String, nullable=False)
    program_type = Column(String, nullable=False)
    
    event_date = Column(Date, nullable=False)
    location = Column(String)
    
    target_audience = Column(String)
    participants_count = Column(Integer)
    
    topics = Column(JSON)
    
    materials_distributed = Column(JSON)
    smoke_alarms_installed = Column(Integer, default=0)
    
    personnel_assigned = Column(JSON)
    
    program_notes = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="OPS")
    created_at = Column(DateTime, default=datetime.utcnow)


class ApparatusMaintenanceRecord(Base):
    __tablename__ = "apparatus_maintenance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    apparatus_id = Column(String, nullable=False)
    apparatus_type = Column(String, nullable=False)
    
    maintenance_date = Column(Date, nullable=False)
    maintenance_type = Column(String, nullable=False)
    
    mileage = Column(Integer)
    hours = Column(Integer)
    
    oil_level_ok = Column(Boolean)
    tire_pressure_ok = Column(Boolean)
    lights_operational = Column(Boolean)
    pump_tested = Column(Boolean)
    
    service_description = Column(Text)
    parts_replaced = Column(JSON)
    
    cost = Column(Float)
    
    performed_by = Column(String)
    
    out_of_service = Column(Boolean, default=False)
    out_of_service_start = Column(DateTime)
    out_of_service_end = Column(DateTime)
    
    next_service_due = Column(Date)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="OPS")
    created_at = Column(DateTime, default=datetime.utcnow)


class FireIncidentSupplement(Base):
    __tablename__ = "fire_incident_supplements"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    incident_id = Column(Integer, ForeignKey("fire_incidents.id"), nullable=False)
    
    water_supply_method = Column(String)
    gallons_used = Column(Integer)
    
    attack_mode = Column(String)
    ventilation_type = Column(String)
    
    incident_command_system_used = Column(Boolean, default=True)
    command_post_location = Column(String)
    
    mutual_aid_received = Column(Boolean, default=False)
    mutual_aid_agencies = Column(JSON)
    
    property_loss_estimate = Column(Float)
    contents_loss_estimate = Column(Float)
    
    fire_cause = Column(String)
    area_of_origin = Column(String)
    ignition_source = Column(String)
    
    investigator_id = Column(Integer, ForeignKey("fire_personnel.id"))
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="OPS")
    created_at = Column(DateTime, default=datetime.utcnow)
