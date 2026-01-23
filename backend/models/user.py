import uuid
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class UserRole(str, Enum):
    founder = "founder"
    admin = "admin"
    crew = "crew"
    billing = "billing"
    compliance = "compliance"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column("passwordHash", String, nullable=False)
    role = Column(String, default=UserRole.crew.value)
    created_at = Column("createdAt", DateTime(timezone=True), server_default=func.now())
