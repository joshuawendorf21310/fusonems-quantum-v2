from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class FleetVehicle(Base):
    __tablename__ = "fleet_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    vehicle_id = Column(String, nullable=False, index=True)
    call_sign = Column(String, default="")
    vehicle_type = Column(String, default="ALS")
    make = Column(String, default="")
    model = Column(String, default="")
    year = Column(String, default="")
    vin = Column(String, default="")
    status = Column(String, default="in_service")
    location = Column(String, default="")
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FleetMaintenance(Base):
    __tablename__ = "fleet_maintenance"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("fleet_vehicles.id"), nullable=False)
    service_type = Column(String, default="maintenance")
    status = Column(String, default="scheduled")
    due_mileage = Column(Integer, default=0)
    notes = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FleetInspection(Base):
    __tablename__ = "fleet_inspections"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("fleet_vehicles.id"), nullable=False)
    status = Column(String, default="pass")
    findings = Column(JSON, nullable=False, default=list)
    performed_by = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FleetTelemetry(Base):
    __tablename__ = "fleet_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("fleet_vehicles.id"), nullable=False)
    latitude = Column(String, default="")
    longitude = Column(String, default="")
    speed = Column(String, default="")
    odometer = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
