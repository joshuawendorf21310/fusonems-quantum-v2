from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class QARubric(Base):
    __tablename__ = "qa_rubrics"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    version = Column(String, default="v1")
    status = Column(String, default="active")
    criteria = Column(JSON, nullable=False, default=list)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QACase(Base):
    __tablename__ = "qa_cases"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    case_type = Column(String, default="clinical")
    priority = Column(String, default="Normal")
    status = Column(String, default="queued")
    trigger = Column(String, default="manual")
    linked_run_id = Column(String, default="")
    linked_patient_id = Column(Integer, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QAReview(Base):
    __tablename__ = "qa_reviews"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("qa_cases.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rubric_id = Column(Integer, ForeignKey("qa_rubrics.id"), nullable=True)
    scores = Column(JSON, nullable=False, default=dict)
    summary = Column(String, default="")
    determination = Column(String, default="pending")
    remediation_required = Column(Boolean, default=False)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QARemediation(Base):
    __tablename__ = "qa_remediations"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("qa_cases.id"), nullable=False)
    plan = Column(String, nullable=False)
    status = Column(String, default="open")
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
