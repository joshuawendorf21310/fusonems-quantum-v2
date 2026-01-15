from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from core.database import Base


class Call(Base):
    __tablename__ = "cad_calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_name = Column(String, nullable=False)
    caller_phone = Column(String, nullable=False)
    location_address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    priority = Column(String, default="Routine")
    status = Column(String, default="Pending")
    eta_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dispatches = relationship("Dispatch", back_populates="call")


class Unit(Base):
    __tablename__ = "cad_units"

    id = Column(Integer, primary_key=True, index=True)
    unit_identifier = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="Available")
    latitude = Column(Float, nullable=False, default=0.0)
    longitude = Column(Float, nullable=False, default=0.0)
    last_update = Column(DateTime(timezone=True), server_default=func.now())

    dispatches = relationship("Dispatch", back_populates="unit")


class Dispatch(Base):
    __tablename__ = "cad_dispatches"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("cad_units.id"), nullable=False)
    status = Column(String, default="Dispatched")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    call = relationship("Call", back_populates="dispatches")
    unit = relationship("Unit", back_populates="dispatches")
