"""Founder Documents (Drive) - files and folders stored in DigitalOcean Spaces."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from core.database import Base


class FounderDocumentFolder(Base):
    __tablename__ = "founder_document_folders"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("founder_document_folders.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FounderDocumentFile(Base):
    __tablename__ = "founder_document_files"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(512), nullable=False)
    storage_key = Column(String(1024), nullable=False, index=True)  # path in Spaces
    mime_type = Column(String(255), default="application/octet-stream")
    size = Column(Integer, default=0)
    folder_id = Column(Integer, ForeignKey("founder_document_folders.id"), nullable=True, index=True)
    tags = Column(JSON, default=list)  # list of strings
    content_key = Column(String(1024), nullable=True)  # optional key for HTML/content (Word doc body)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
