from sqlalchemy import Column, DateTime, String, Integer, func

from core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column("createdAt", DateTime(timezone=True), server_default=func.now())
