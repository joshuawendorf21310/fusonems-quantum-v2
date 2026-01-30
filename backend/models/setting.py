import uuid

from sqlalchemy import Column, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class Setting(Base):
    __tablename__ = "settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column("orgId", Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False, default=dict)
