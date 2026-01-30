from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from core.config import settings
from models.validation import ValidationRule, DataValidationIssue
from models.epcr_core import Patient, NEMSISValidationStatus, EpcrVisibilityRule
from models.exports import ExportJob
from services.storage.health_service import StorageHealthService
from utils.logger import logger


class SystemHealthService:
    
    @staticmethod
    def get_validation_rules_health(db: Session, org_id: int) -> Dict[str, Any]:
        try:
            total_rules = db.query(ValidationRule).filter(
                ValidationRule.org_id == org_id
            ).count()
            
            active_rules = db.query(ValidationRule).filter(
                and_(
                    ValidationRule.org_id == org_id,
                    ValidationRule.status == "active"
                )
            ).count()
            
            inactive_rules = total_rules - active_rules
            
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            open_issues = db.query(DataValidationIssue).filter(
                and_(
                    DataValidationIssue.org_id == org_id,
                    DataValidationIssue.status == "Open"
                )
            ).count()
            
            recent_issues = db.query(DataValidationIssue).filter(
                and_(
                    DataValidationIssue.org_id == org_id,
                    DataValidationIssue.created_at >= twenty_four_hours_ago
                )
            ).count()
            
            high_severity_issues = db.query(DataValidationIssue).filter(
                and_(
                    DataValidationIssue.org_id == org_id,
                    DataValidationIssue.status == "Open",
                    DataValidationIssue.severity == "High"
                )
            ).count()
            
            if high_severity_issues > 10:
                status = "CRITICAL"
                message = f"{high_severity_issues} high-severity validation issues"
            elif high_severity_issues > 5:
                status = "DEGRADED"
                message = f"{high_severity_issues} high-severity validation issues"
            elif open_issues > 50:
                status = "WARNING"
                message = f"{open_issues} open validation issues"
            else:
                status = "HEALTHY"
                message = "Validation system operating normally"
            
            return {
                "status": status,
                "message": message,
                "metrics": {
                    "total_rules": total_rules,
                    "active_rules": active_rules,
                    "inactive_rules": inactive_rules,
                    "open_issues": open_issues,
                    "recent_issues_24h": recent_issues,
                    "high_severity_issues": high_severity_issues
                }
            }
        except Exception as e:
            logger.error(f"Failed to get validation rules health: {e}")
            return {
                "status": "UNKNOWN",
                "message": f"Health check failed: {str(e)}",
                "metrics": {}
            }
    
    @staticmethod
    def get_nemsis_system_health(db: Session, org_id: int) -> Dict[str, Any]:
        try:
            total_patients = db.query(Patient).filter(
                Patient.org_id == org_id
            ).count()
            
            finalized_patients = db.query(Patient).filter(
                and_(
                    Patient.org_id == org_id,
                    Patient.status == "billing_ready"
                )
            ).count()
            
            locked_charts = db.query(Patient).filter(
                and_(
                    Patient.org_id == org_id,
                    Patient.chart_locked == True
                )
            ).count()
            
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            recent_charts = db.query(Patient).filter(
                and_(
                    Patient.org_id == org_id,
                    Patient.created_at >= twenty_four_hours_ago
                )
            ).count()
            
            avg_qa_score = db.query(func.avg(Patient.qa_score)).filter(
                Patient.org_id == org_id
            ).scalar() or 0
            
            if avg_qa_score < 70:
                status = "DEGRADED"
                message = f"Low average QA score: {avg_qa_score:.1f}"
            elif finalized_patients == 0 and total_patients > 0:
                status = "WARNING"
                message = "No patients billing-ready"
            else:
                status = "HEALTHY"
                message = "NEMSIS system operating normally"
            
            return {
                "status": status,
                "message": message,
                "metrics": {
                    "total_patients": total_patients,
                    "finalized_patients": finalized_patients,
                    "locked_charts": locked_charts,
                    "recent_charts_24h": recent_charts,
                    "avg_qa_score": round(avg_qa_score, 1)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get NEMSIS system health: {e}")
            return {
                "status": "UNKNOWN",
                "message": f"Health check failed: {str(e)}",
                "metrics": {}
            }
    
    @staticmethod
    def get_export_system_health(db: Session, org_id: int) -> Dict[str, Any]:
        try:
            from models.exports import ExportJob
            
            total_exports = db.query(ExportJob).filter(
                ExportJob.org_id == org_id
            ).count()
            
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            recent_exports = db.query(ExportJob).filter(
                and_(
                    ExportJob.org_id == org_id,
                    ExportJob.created_at >= twenty_four_hours_ago
                )
            ).count()
            
            failed_exports = db.query(ExportJob).filter(
                and_(
                    ExportJob.org_id == org_id,
                    ExportJob.status == "failed",
                    ExportJob.created_at >= twenty_four_hours_ago
                )
            ).count()
            
            pending_exports = db.query(ExportJob).filter(
                and_(
                    ExportJob.org_id == org_id,
                    ExportJob.status.in_(["pending", "processing"])
                )
            ).count()
            
            completed_exports = db.query(ExportJob).filter(
                and_(
                    ExportJob.org_id == org_id,
                    ExportJob.status == "completed",
                    ExportJob.created_at >= twenty_four_hours_ago
                )
            ).count()
            
            failure_rate = (failed_exports / recent_exports * 100) if recent_exports > 0 else 0
            
            if failure_rate > 20:
                status = "CRITICAL"
                message = f"High export failure rate: {failure_rate:.1f}%"
            elif failure_rate > 10:
                status = "DEGRADED"
                message = f"Elevated export failure rate: {failure_rate:.1f}%"
            elif pending_exports > 10:
                status = "WARNING"
                message = f"{pending_exports} exports pending"
            else:
                status = "HEALTHY"
                message = "Export system operating normally"
            
            return {
                "status": status,
                "message": message,
                "metrics": {
                    "total_exports": total_exports,
                    "recent_exports_24h": recent_exports,
                    "failed_exports_24h": failed_exports,
                    "pending_exports": pending_exports,
                    "completed_exports_24h": completed_exports,
                    "failure_rate_pct": round(failure_rate, 1)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get export system health: {e}")
            return {
                "status": "UNKNOWN",
                "message": f"Health check failed: {str(e)}",
                "metrics": {}
            }
    
    @staticmethod
    def get_email_health() -> Dict[str, Any]:
        """Check founder email (SMTP/IMAP) configuration."""
        try:
            smtp_ok = bool(
                getattr(settings, "SMTP_HOST", None)
                and getattr(settings, "SMTP_USERNAME", None)
                and getattr(settings, "SMTP_PASSWORD", None)
            )
            imap_ok = bool(
                getattr(settings, "IMAP_HOST", None)
                and getattr(settings, "IMAP_USERNAME", None)
                and getattr(settings, "IMAP_PASSWORD", None)
            )
            if smtp_ok and imap_ok:
                status, message = "HEALTHY", "SMTP and IMAP configured"
            elif smtp_ok:
                status, message = "WARNING", "SMTP configured; IMAP not configured (inbound poll unavailable)"
            elif imap_ok:
                status, message = "WARNING", "IMAP configured; SMTP not configured (sending unavailable)"
            else:
                status, message = "DEGRADED", "Email not configured (set SMTP_* and IMAP_*)"
            return {
                "status": status,
                "message": message,
                "metrics": {
                    "smtp_configured": 1 if smtp_ok else 0,
                    "imap_configured": 1 if imap_ok else 0,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get email health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_spaces_health() -> Dict[str, Any]:
        """Check DigitalOcean Spaces (founder documents) configuration."""
        try:
            ok = bool(
                getattr(settings, "SPACES_BUCKET", None)
                and getattr(settings, "SPACES_ENDPOINT", None)
                and getattr(settings, "SPACES_ACCESS_KEY", None)
                and getattr(settings, "SPACES_SECRET_KEY", None)
            )
            if ok:
                status, message = "HEALTHY", "Spaces configured for documents"
            else:
                status, message = "DEGRADED", "Spaces not configured (documents upload/save will fail)"
            return {
                "status": status,
                "message": message,
                "metrics": {"configured": 1 if ok else 0},
            }
        except Exception as e:
            logger.error(f"Failed to get Spaces health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_telnyx_health() -> Dict[str, Any]:
        """Check Telnyx (IVR/phone/fax) configuration."""
        try:
            enabled = getattr(settings, "TELNYX_ENABLED", False)
            key_ok = bool(getattr(settings, "TELNYX_API_KEY", None))
            from_ok = bool(getattr(settings, "TELNYX_FROM_NUMBER", None))
            if enabled and key_ok and from_ok:
                status, message = "HEALTHY", "Telnyx configured for IVR/phone"
            elif enabled and key_ok:
                status, message = "WARNING", "Telnyx enabled but TELNYX_FROM_NUMBER not set"
            elif enabled:
                status, message = "DEGRADED", "Telnyx enabled but API key not set"
            else:
                status, message = "HEALTHY", "Telnyx disabled (optional)"
            return {
                "status": status,
                "message": message,
                "metrics": {"enabled": 1 if enabled else 0, "configured": 1 if (key_ok and from_ok) else 0},
            }
        except Exception as e:
            logger.error(f"Failed to get Telnyx health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_ollama_health() -> Dict[str, Any]:
        """Check Ollama (AI biller / billing explain) configuration."""
        try:
            enabled = getattr(settings, "OLLAMA_ENABLED", False)
            url = getattr(settings, "OLLAMA_SERVER_URL", None) or ""
            url_ok = bool(url.strip())
            if not enabled:
                status, message = "HEALTHY", "Ollama disabled (optional)"
            elif url_ok:
                status, message = "HEALTHY", "Ollama configured for AI/IVR"
            else:
                status, message = "WARNING", "Ollama enabled but OLLAMA_SERVER_URL not set"
            return {
                "status": status,
                "message": message,
                "metrics": {"enabled": 1 if enabled else 0, "url_configured": 1 if url_ok else 0},
            }
        except Exception as e:
            logger.error(f"Failed to get Ollama health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_nemsis_dataset_health(db: Session, org_id: int) -> Dict[str, Any]:
        """NEMSIS v3.5 dataset / mapper availability (reference elements for ePCR)."""
        try:
            from services.epcr.nemsis_mapper import NEMSISElement
            elements_defined = len(NEMSISElement)
            status = "HEALTHY"
            message = f"NEMSIS v3.5 mapper active ({elements_defined} elements)"
            return {
                "status": status,
                "message": message,
                "metrics": {"elements_defined": elements_defined},
            }
        except Exception as e:
            logger.error(f"Failed to get NEMSIS dataset health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_visibility_builder_health(db: Session, org_id: int) -> Dict[str, Any]:
        """Visibility builder (ePCR field visibility rules)."""
        try:
            total = db.query(EpcrVisibilityRule).filter(EpcrVisibilityRule.org_id == org_id).count()
            active = db.query(EpcrVisibilityRule).filter(
                EpcrVisibilityRule.org_id == org_id, EpcrVisibilityRule.active == True
            ).count()
            status = "HEALTHY"
            message = f"{active} active visibility rules" if total else "No visibility rules defined"
            return {
                "status": status,
                "message": message,
                "metrics": {"total_rules": total, "active_rules": active},
            }
        except Exception as e:
            logger.error(f"Failed to get visibility builder health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_snomed_health() -> Dict[str, Any]:
        """SNOMED CT dataset / API availability (procedure/finding codes)."""
        try:
            # No SNOMED table or API in codebase yet; suggestions limited
            loaded = bool(getattr(settings, "SNOMED_API_URL", None) or getattr(settings, "SNOMED_DATASET_LOADED", False))
            if loaded:
                status, message = "HEALTHY", "SNOMED dataset/API configured"
            else:
                status, message = "WARNING", "SNOMED not loaded; procedure/finding suggestions limited"
            return {
                "status": status,
                "message": message,
                "metrics": {"loaded": 1 if loaded else 0},
            }
        except Exception as e:
            logger.error(f"Failed to get SNOMED health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_icd10_health() -> Dict[str, Any]:
        """ICD-10 reference availability (diagnosis codes)."""
        try:
            # Billing assist uses keyword heuristics; full dataset optional
            full_loaded = bool(getattr(settings, "ICD10_DATASET_LOADED", False) or getattr(settings, "ICD10_API_URL", None))
            if full_loaded:
                status, message = "HEALTHY", "ICD-10 dataset/API configured"
            else:
                status, message = "WARNING", "ICD-10 heuristics only; full dataset not loaded"
            return {
                "status": status,
                "message": message,
                "metrics": {"full_dataset": 1 if full_loaded else 0},
            }
        except Exception as e:
            logger.error(f"Failed to get ICD-10 health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_rxnorm_health() -> Dict[str, Any]:
        """RXNorm dataset / API availability (medication codes)."""
        try:
            loaded = bool(getattr(settings, "RXNORM_API_URL", None) or getattr(settings, "RXNORM_DATASET_LOADED", False))
            if loaded:
                status, message = "HEALTHY", "RXNorm dataset/API configured"
            else:
                status, message = "WARNING", "RXNorm not loaded; medication suggestions limited"
            return {
                "status": status,
                "message": message,
                "metrics": {"loaded": 1 if loaded else 0},
            }
        except Exception as e:
            logger.error(f"Failed to get RXNorm health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_nemsis_state_export_health() -> Dict[str, Any]:
        """NEMSIS export and state submission: payload on finalize; state submit needs endpoint config (Wisconsin-first)."""
        try:
            export_available = True  # NEMSISExporter.export_record_to_nemsis runs on ePCR finalize
            state_endpoints = getattr(settings, "NEMSIS_STATE_ENDPOINTS", None)
            wi_endpoint = getattr(settings, "WISCONSIN_NEMSIS_ENDPOINT", None)
            state_codes = getattr(settings, "NEMSIS_STATE_CODES", None) or "WI"
            state_configured = bool(state_endpoints or (wi_endpoint and "WI" in (state_codes or "")))
            if export_available and state_configured:
                status, message = "HEALTHY", "NEMSIS export on finalize; state endpoints configured"
            elif export_available:
                status, message = "WARNING", "NEMSIS export on finalize; set NEMSIS_STATE_CODES/endpoints for state submit"
            else:
                status, message = "DEGRADED", "NEMSIS export not available"
            return {
                "status": status,
                "message": message,
                "metrics": {"export_on_finalize": 1 if export_available else 0, "state_configured": 1 if state_configured else 0},
            }
        except Exception as e:
            logger.error(f"Failed to get NEMSIS/state export health: {e}")
            return {"status": "UNKNOWN", "message": str(e), "metrics": {}}

    @staticmethod
    def get_builder_systems_health(db: Session, org_id: int) -> Dict[str, Any]:
        """All builder + founder service checks: validation, NEMSIS, exports, email, Spaces, Telnyx, Ollama, datasets."""
        return {
            "validation_rules": SystemHealthService.get_validation_rules_health(db, org_id),
            "nemsis": SystemHealthService.get_nemsis_system_health(db, org_id),
            "exports": SystemHealthService.get_export_system_health(db, org_id),
            "email": SystemHealthService.get_email_health(),
            "spaces": SystemHealthService.get_spaces_health(),
            "telnyx": SystemHealthService.get_telnyx_health(),
            "ollama": SystemHealthService.get_ollama_health(),
            "nemsis_dataset": SystemHealthService.get_nemsis_dataset_health(db, org_id),
            "visibility_builder": SystemHealthService.get_visibility_builder_health(db, org_id),
            "snomed": SystemHealthService.get_snomed_health(),
            "icd10": SystemHealthService.get_icd10_health(),
            "rxnorm": SystemHealthService.get_rxnorm_health(),
            "nemsis_state_export": SystemHealthService.get_nemsis_state_export_health(),
        }
    
    @staticmethod
    def get_unified_system_health(db: Session, org_id: int) -> Dict[str, Any]:
        storage_health = StorageHealthService.get_storage_health(db, org_id=str(org_id))
        builders = SystemHealthService.get_builder_systems_health(db, org_id)

        all_statuses = [
            storage_health["status"],
            builders["validation_rules"]["status"],
            builders["nemsis"]["status"],
            builders["exports"]["status"],
            builders["email"]["status"],
            builders["spaces"]["status"],
            builders["telnyx"]["status"],
            builders["ollama"]["status"],
            builders["nemsis_dataset"]["status"],
            builders["visibility_builder"]["status"],
            builders["snomed"]["status"],
            builders["icd10"]["status"],
            builders["rxnorm"]["status"],
            builders["nemsis_state_export"]["status"],
        ]

        if "CRITICAL" in all_statuses:
            overall_status = "CRITICAL"
            overall_message = "One or more critical systems degraded"
        elif "DEGRADED" in all_statuses:
            overall_status = "DEGRADED"
            overall_message = "One or more systems degraded"
        elif "WARNING" in all_statuses:
            overall_status = "WARNING"
            overall_message = "One or more systems have warnings"
        elif "UNKNOWN" in all_statuses:
            overall_status = "WARNING"
            overall_message = "Unable to determine health of one or more systems"
        else:
            overall_status = "HEALTHY"
            overall_message = "All systems healthy"

        critical_issues = []
        warnings = []

        for system_name, system_data in {
            "Storage": storage_health,
            "Validation Rules": builders["validation_rules"],
            "NEMSIS": builders["nemsis"],
            "Exports": builders["exports"],
            "Email": builders["email"],
            "Spaces": builders["spaces"],
            "Telnyx": builders["telnyx"],
            "Ollama": builders["ollama"],
            "NEMSIS Dataset": builders["nemsis_dataset"],
            "Visibility Builder": builders["visibility_builder"],
            "SNOMED": builders["snomed"],
            "ICD-10": builders["icd10"],
            "RXNorm": builders["rxnorm"],
            "NEMSIS/State Export": builders["nemsis_state_export"],
        }.items():
            if system_data["status"] == "CRITICAL":
                critical_issues.append(f"{system_name}: {system_data['message']}")
            elif system_data["status"] in ["DEGRADED", "WARNING"]:
                warnings.append(f"{system_name}: {system_data['message']}")

        return {
            "overall_status": overall_status,
            "overall_message": overall_message,
            "timestamp": datetime.utcnow().isoformat(),
            "subsystems": {
                "storage": storage_health,
                "validation_rules": builders["validation_rules"],
                "nemsis": builders["nemsis"],
                "exports": builders["exports"],
                "email": builders["email"],
                "spaces": builders["spaces"],
                "telnyx": builders["telnyx"],
                "ollama": builders["ollama"],
                "nemsis_dataset": builders["nemsis_dataset"],
                "visibility_builder": builders["visibility_builder"],
                "snomed": builders["snomed"],
                "icd10": builders["icd10"],
                "rxnorm": builders["rxnorm"],
                "nemsis_state_export": builders["nemsis_state_export"],
            },
            "critical_issues": critical_issues,
            "warnings": warnings,
            "requires_immediate_attention": len(critical_issues) > 0,
        }
