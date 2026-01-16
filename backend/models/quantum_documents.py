from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class DocumentFolder(Base):
    __tablename__ = "documents_folders"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    parent_id = Column(String, ForeignKey("documents_folders.id"), nullable=True)
    name = Column(String, nullable=False)
    path_slug = Column(String, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RetentionPolicy(Base):
    __tablename__ = "retention_policies"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    applies_to = Column(String, default="general")
    retention_days = Column(Integer, nullable=True)
    delete_behavior = Column(String, default="soft_delete")
    legal_hold_behavior = Column(String, default="always_freeze")
    status = Column(String, default="active")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DocumentFile(Base):
    __tablename__ = "documents_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    folder_id = Column(String, ForeignKey("documents_folders.id"), nullable=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, default="application/octet-stream")
    size_bytes = Column(Integer, default=0)
    storage_key = Column(String, nullable=False, index=True)
    sha256 = Column(String, nullable=False)
    classification = Column(String, default="ops")
    tags = Column(JSON, nullable=False, default=list)
    status = Column(String, default="ACTIVE")
    retention_policy_id = Column(Integer, ForeignKey("retention_policies.id"), nullable=True)
    legal_hold_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DocumentVersion(Base):
    __tablename__ = "documents_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    file_id = Column(String, ForeignKey("documents_files.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    storage_key = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    size_bytes = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentPermission(Base):
    __tablename__ = "documents_permissions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    subject_type = Column(String, nullable=False)
    subject_id = Column(Integer, nullable=True)
    subject_key = Column(String, nullable=True)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    permission = Column(String, nullable=False)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DiscoveryExport(Base):
    __tablename__ = "discovery_exports"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    hold_id = Column(Integer, ForeignKey("legal_holds.id"), nullable=True)
    export_type = Column(String, default="custom_search")
    filters = Column(JSON, nullable=False, default=dict)
    status = Column(String, default="queued")
    storage_key = Column(String, default="")
    sha256 = Column(String, default="")
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
