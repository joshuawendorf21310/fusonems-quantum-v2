from sqlalchemy import Column, Integer, String, DateTime, func
from core.database import Base

class Dispatch(Base):
    __tablename__ = "dispatch_log"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(String, nullable=False)
    call_id = Column(String, nullable=False)
    status = Column(String, default="Dispatched")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
