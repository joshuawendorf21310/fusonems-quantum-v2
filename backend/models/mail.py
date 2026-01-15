from sqlalchemy import Column, DateTime, Integer, String, Text, func

from core.database import Base


class Message(Base):
    __tablename__ = "mail_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String, default="Queued")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
