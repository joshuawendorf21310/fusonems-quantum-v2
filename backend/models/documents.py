from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from core.database import Base


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    module_key = Column(String, nullable=False, index=True)
    template_version = Column(String, default="v1")
    status = Column(String, default="draft")
    jurisdiction = Column(String, default="default")
    sections = Column(JSON, nullable=False, default=list)
    classification = Column(String, default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=False)
    title = Column(String, nullable=False)
    output_format = Column(String, default="PDF")
    status = Column(String, default="draft")
    content = Column(JSON, nullable=False, default=dict)
    provenance = Column(JSON, nullable=False, default=dict)
    document_hash = Column(String, default="")
    legal_hold = Column(Boolean, default=False)
    classification = Column(String, default="NON_PHI")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
