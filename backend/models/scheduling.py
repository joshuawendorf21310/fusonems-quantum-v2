from sqlalchemy import Column, DateTime, Integer, JSON, String, func

from core.database import Base


class Shift(Base):
    __tablename__ = "schedule_shifts"

    id = Column(Integer, primary_key=True, index=True)
    crew_name = Column(String, nullable=False)
    shift_start = Column(DateTime(timezone=True), nullable=False)
    shift_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="Scheduled")
    certifications = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
