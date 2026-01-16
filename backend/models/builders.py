from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class BuilderRegistry(Base):
    __tablename__ = "builder_registry"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    builder_key = Column(String, nullable=False, index=True)
    version = Column(String, default="v1")
    status = Column(String, default="active")
    description = Column(String, default="")
    impacted_modules = Column(JSON, nullable=False, default=list)
    last_changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BuilderChangeLog(Base):
    __tablename__ = "builder_change_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    builder_key = Column(String, nullable=False, index=True)
    change_summary = Column(String, nullable=False)
    before_state = Column(JSON, nullable=False, default=dict)
    after_state = Column(JSON, nullable=False, default=dict)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
