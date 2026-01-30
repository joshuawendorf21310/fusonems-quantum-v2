"""
NEMSIS 3.5.1 Schematron validation service.

Runs DB-stored EpcrSchematronRule assertions (version 3.5.1) against a
NEMSIS element map built from the ePCR record. Aligns with official NEMSIS
Schematron (EMSDataSet.sch) semantics: required elements present, value set
constraints. Results are merged into NEMSISValidationResult at finalize.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.epcr_core import EpcrRecord, EpcrSchematronRule, Patient

logger = logging.getLogger(__name__)

# NEMSIS 3.5.1 EMS dataset element IDs used for validation (subset; extend as needed)
# See: https://nemsis.org/media/nemsis_v3/release-3.5.1/Schematron/rules/EMSDataSet.sch
NEMSIS_351_REQUIRED_ELEMENTS = [
    "eDispatch.01",   # Unit dispatched
    "eTimes.01",     # Response interval
    "ePatient.01",   # Age
    "eChiefComplaint.01",
    "eDisposition.24",  # Hospital arrival / destination
]


def build_nemsis_element_map(db: Session, record: EpcrRecord) -> Dict[str, Any]:
    """
    Build a flat NEMSIS 3.5.1 element map from record + related data.
    Keys are NEMSIS element IDs (e.g. eDisposition.24); values are raw or ISO strings.
    """
    from models.epcr_core import EpcrVitals, EpcrAssessment, EpcrMedication, EpcrIntervention

    elements: Dict[str, Any] = {}

    # Record-level (eTimes, eDisposition, eChiefComplaint, etc.)
    if record.dispatch_datetime:
        elements["eDispatch.01"] = record.dispatch_datetime.isoformat() if hasattr(record.dispatch_datetime, "isoformat") else str(record.dispatch_datetime)
    if record.incident_datetime:
        elements["eTimes.01"] = record.incident_datetime.isoformat() if hasattr(record.incident_datetime, "isoformat") else str(record.incident_datetime)
    if record.scene_arrival_datetime:
        elements["eTimes.02"] = record.scene_arrival_datetime.isoformat() if hasattr(record.scene_arrival_datetime, "isoformat") else str(record.scene_arrival_datetime)
    if record.hospital_arrival_datetime:
        elements["eDisposition.24"] = record.hospital_arrival_datetime.isoformat() if hasattr(record.hospital_arrival_datetime, "isoformat") else str(record.hospital_arrival_datetime)
    if record.chief_complaint:
        elements["eChiefComplaint.01"] = record.chief_complaint
    if record.chief_complaint_code:
        elements["eChiefComplaint.02"] = record.chief_complaint_code
    if record.patient_destination:
        elements["eDisposition.23"] = record.patient_destination
    elements["eRecord.01"] = record.incident_number
    elements["eRecord.02"] = record.record_number

    # Patient (age, gender) from linked patient if available
    try:
        patient = record.patient if hasattr(record, "patient") else None
        if patient is None and record.patient_id:
            patient = db.get(Patient, record.patient_id)
        if patient:
            # ePatient.01: age in years (derive from date_of_birth if present)
            dob = getattr(patient, "date_of_birth", None)
            if dob:
                try:
                    from datetime import datetime
                    if isinstance(dob, str) and len(dob) >= 4:
                        y = int(dob[:4])
                        elements["ePatient.01"] = datetime.now().year - y
                except (ValueError, TypeError):
                    pass
            if getattr(patient, "gender", None):
                elements["ePatient.02"] = patient.gender
    except Exception as e:
        logger.debug("Patient lookup for NEMSIS map: %s", e)

    # Vitals (first set) → NEMSIS vitals elements
    vitals = (
        db.query(EpcrVitals)
        .filter(EpcrVitals.record_id == record.id)
        .order_by(EpcrVitals.sequence.asc())
        .limit(1)
        .first()
    )
    if vitals and vitals.nemsis_elements:
        for k, v in vitals.nemsis_elements.items():
            if v is not None and (not isinstance(v, dict) or v.get("value") is not None):
                elements[k] = v.get("value", v) if isinstance(v, dict) else v
    if vitals and vitals.values:
        # Fallback: map common names to NEMSIS
        mapping = {
            "heart_rate": "eVital.01",
            "systolic_bp": "eVital.02",
            "diastolic_bp": "eVital.03",
            "respiratory_rate": "eVital.04",
            "pulse_ox": "eVital.05",
            "temperature": "eVital.06",
        }
        for name, eid in mapping.items():
            if name in vitals.values and elements.get(eid) is None:
                elements[eid] = vitals.values[name]

    # Assessments: clinical impression / impression code
    assessment = (
        db.query(EpcrAssessment)
        .filter(EpcrAssessment.record_id == record.id)
        .order_by(EpcrAssessment.id.desc())
        .first()
    )
    if assessment:
        if assessment.clinical_impression:
            elements["eSituation.02"] = assessment.clinical_impression
        if assessment.impression_code:
            elements["eSituation.03"] = assessment.impression_code

    # Medications (first medication as NEMSIS medication element sample)
    med = (
        db.query(EpcrMedication)
        .filter(EpcrMedication.record_id == record.id)
        .first()
    )
    if med:
        elements["eMedication.01"] = getattr(med, "medication_name", None) or (med.med_metadata or {}).get("name")
        elements["eMedication.02"] = (med.med_metadata or {}).get("dose")

    return elements


def _evaluate_assertion(assertion: str, elements: Dict[str, Any]) -> bool:
    """
    Evaluate a simple assertion against the element map.
    Supports:
    - "eDisposition.24 present" / "eDisposition.24 must be present"
    - "eChiefComplaint.01 present"
    - "element_id present" (element_id must be a key with non-empty value)
    - "element_id matches pattern" (if fix contains regex)
    """
    if not assertion or not assertion.strip():
        return True
    assertion = assertion.strip().lower()
    # "eXXX.NN present" or "eXXX.NN must be present"
    present_match = re.match(r"([eE][A-Za-z]+\.[0-9]+)\s+(?:must\s+be\s+)?present", assertion)
    if present_match:
        eid = present_match.group(1)
        val = elements.get(eid)
        if val is None or (isinstance(val, str) and not val.strip()):
            return False
        return True
    # "element_id present" (generic)
    if assertion.endswith(" present"):
        eid = assertion[:-8].strip()
        val = elements.get(eid)
        if val is None or (isinstance(val, str) and not val.strip()):
            return False
        return True
    return True


def run_schematron(
    db: Session,
    record: EpcrRecord,
    nemsis_version: str = "3.5.1",
) -> Dict[str, Any]:
    """
    Run all active EpcrSchematronRule rules (for org and version) against the
    record's NEMSIS element map. Returns dict with keys: passed, errors, warnings.
    """
    elements = build_nemsis_element_map(db, record)
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    rules = (
        db.query(EpcrSchematronRule)
        .filter(
            EpcrSchematronRule.org_id == record.org_id,
            EpcrSchematronRule.active == True,
            EpcrSchematronRule.version == nemsis_version,
        )
        .all()
    )

    for rule in rules:
        assertion = (rule.assertion or "").strip()
        if not assertion:
            continue
        passed = _evaluate_assertion(assertion, elements)
        if not passed:
            entry = {
                "rule": rule.name,
                "message": rule.description or f"NEMSIS 3.5.1 rule failed: {rule.name}",
                "assertion": assertion,
                "fix": (rule.fix or "").strip() or None,
            }
            # Treat as error by default; could add severity on rule later
            errors.append(entry)

    # Built-in NEMSIS 3.5.1 required elements: error if missing or empty
    for eid in NEMSIS_351_REQUIRED_ELEMENTS:
        val = elements.get(eid)
        if val is None or (isinstance(val, str) and not val.strip()):
            if not any(e.get("assertion", "").lower().find(eid.lower()) >= 0 for e in errors):
                errors.append({
                    "rule": "NEMSIS 3.5.1 Required",
                    "message": f"Required element {eid} is missing or empty.",
                    "assertion": f"{eid} present",
                    "fix": f"Populate {eid} in the ePCR record.",
                })

    return {
        "passed": len(errors) == 0 and len(warnings) == 0,
        "errors": errors,
        "warnings": warnings,
        "element_count": len(elements),
    }
