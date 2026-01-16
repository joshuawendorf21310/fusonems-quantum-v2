from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, default="medical")
    sku = Column(String, default="")
    manufacturer = Column(String, default="")
    unit = Column(String, default="")
    par_level = Column(Integer, default=0)
    quantity_on_hand = Column(Integer, default=0)
    location = Column(String, default="")
    status = Column(String, default="in_stock")
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    movement_type = Column(String, default="transfer")
    quantity = Column(Integer, default=0)
    from_location = Column(String, default="")
    to_location = Column(String, default="")
    reason = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryRigCheck(Base):
    __tablename__ = "inventory_rig_checks"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    unit_id = Column(String, default="")
    status = Column(String, default="pass")
    findings = Column(JSON, nullable=False, default=list)
    performed_by = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
