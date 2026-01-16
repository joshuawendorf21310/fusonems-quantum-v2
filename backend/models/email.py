from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from core.database import Base


class EmailThread(Base):
    __tablename__ = "email_threads"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    subject = Column(String, default="")
    normalized_subject = Column(String, default="", index=True)
    status = Column(String, default="open")
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"), nullable=False, index=True)
    classification = Column(String, default="ops")
    direction = Column(String, default="inbound")
    status = Column(String, default="queued")
    sender = Column(String, default="")
    recipients = Column(JSON, nullable=False, default=list)
    cc = Column(JSON, nullable=False, default=list)
    bcc = Column(JSON, nullable=False, default=list)
    subject = Column(String, default="")
    normalized_subject = Column(String, default="", index=True)
    body_plain = Column(Text, default="")
    body_html = Column(Text, default="")
    message_id = Column(String, default="", index=True)
    in_reply_to = Column(String, default="", index=True)
    references = Column(JSON, nullable=False, default=list)
    postmark_message_id = Column(String, default="", index=True)
    postmark_record_type = Column(String, default="")
    meta = Column(JSON, nullable=False, default=dict)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailLabel(Base):
    __tablename__ = "email_labels"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, index=True)
    color = Column(String, default="orange")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailMessageLabel(Base):
    __tablename__ = "email_message_labels"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=False, index=True)
    label_id = Column(Integer, ForeignKey("email_labels.id"), nullable=False, index=True)
    applied_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    applied_by_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailAttachmentLink(Base):
    __tablename__ = "email_attachment_links"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents_files.id"), nullable=False, index=True)
    filename = Column(String, default="")
    content_type = Column(String, default="application/octet-stream")
    size_bytes = Column(Integer, default=0)
    sha256 = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
