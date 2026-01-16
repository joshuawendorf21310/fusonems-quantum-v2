from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class TrainingCourse(Base):
    __tablename__ = "training_courses"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    category = Column(String, default="clinical")
    status = Column(String, default="active")
    version = Column(String, default="v1")
    prerequisites = Column(JSON, nullable=False, default=list)
    credit_hours = Column(Integer, default=0)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrainingEnrollment(Base):
    __tablename__ = "training_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("training_courses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="assigned")
    score = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CredentialRecord(Base):
    __tablename__ = "credential_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credential_type = Column(String, nullable=False)
    issuer = Column(String, default="")
    license_number = Column(String, default="")
    status = Column(String, default="active")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SkillCheckoff(Base):
    __tablename__ = "skill_checkoffs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    evaluator = Column(String, default="")
    status = Column(String, default="pending")
    score = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CERecord(Base):
    __tablename__ = "ce_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, default="state")
    hours = Column(Integer, default=0)
    status = Column(String, default="pending")
    cycle = Column(String, default="2024")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
