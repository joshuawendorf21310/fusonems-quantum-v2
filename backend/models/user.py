from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, func

from core.database import Base


class UserRole(str, Enum):
    admin = "admin"
    dispatcher = "dispatcher"
    provider = "provider"
    investor = "investor"
    founder = "founder"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.dispatcher.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
