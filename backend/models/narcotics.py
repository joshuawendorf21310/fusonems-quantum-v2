from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class NarcoticItem(Base):
    __tablename__ = "narcotic_items"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    schedule = Column(String, default="II")
    concentration = Column(String, default="")
    lot_number = Column(String, default="")
    expiration_date = Column(String, default="")
    quantity = Column(String, default="0")
    storage_location = Column(String, default="")
    status = Column(String, default="in_service")
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NarcoticCustodyEvent(Base):
    __tablename__ = "narcotic_custody_events"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    narcotic_id = Column(Integer, ForeignKey("narcotic_items.id"), nullable=False)
    event_type = Column(String, nullable=False)
    from_location = Column(String, default="")
    to_location = Column(String, default="")
    quantity = Column(String, default="0")
    witness = Column(String, default="")
    notes = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NarcoticDiscrepancy(Base):
    __tablename__ = "narcotic_discrepancies"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    narcotic_id = Column(Integer, ForeignKey("narcotic_items.id"), nullable=False)
    severity = Column(String, default="High")
    status = Column(String, default="open")
    summary = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
