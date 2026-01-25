import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column("orgId", UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column("userId", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column("entityType", String, nullable=False, index=True)
    entity_id = Column("entityId", String, nullable=False, index=True)
    meta_data = Column("metadata", JSON, nullable=False, default=dict)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
