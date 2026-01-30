"""
Terminology Builder - NEMSIS-constrained ICD-10, SNOMED, RXNorm.

Founders can add/remove/adjust codes for:
- ICD-10: diagnosis (chief complaint); NEMSIS element ref for validation.
- SNOMED: interventions/procedures; NEMSIS procedure elements.
- RXNorm: medications; NEMSIS medication elements.

All entries follow NEMSIS constraints (nemsis_element_ref) so exports stay compliant.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func

from core.database import Base


class TerminologyEntry(Base):
    __tablename__ = "terminology_builder"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Code set: icd10, snomed, rxnorm
    code_set = Column(String(32), nullable=False, index=True)
    # Use case: diagnosis, intervention, medication (for filtering)
    use_case = Column(String(32), nullable=False, default="diagnosis", index=True)

    # Code and display (e.g. R07.9, 1234567890, 315090)
    code = Column(String(128), nullable=False, index=True)
    description = Column(String(512), nullable=False)
    # Alternate wording founders can adjust
    alternate_text = Column(String(512), nullable=True)

    # NEMSIS constraint: which NEMSIS element this maps to (e.g. eChiefComplaint.01, eMedications.01)
    nemsis_element_ref = Column(String(128), nullable=True, index=True)
    # Optional: NEMSIS value set or state-accepted list reference
    nemsis_value_set = Column(String(128), nullable=True)

    active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
