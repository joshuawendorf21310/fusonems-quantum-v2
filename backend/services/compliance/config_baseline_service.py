"""
Configuration Baseline Service for FedRAMP CM-2, CM-6 Compliance

This service provides:
- Capture current system configuration
- Compare to baseline configurations
- Detect configuration drift
- Generate drift reports
- Automated remediation suggestions
"""
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.logger import logger
from models.configuration import (
    ConfigurationBaseline,
    ConfigurationComplianceStatus,
    ComplianceStatus,
    DriftSeverity,
)
from services.compliance.configuration_management import ConfigurationManagementService


class ConfigurationBaselineService:
    """
    Service for capturing configurations and detecting drift.
    
    Implements FedRAMP CM-2 and CM-6 controls.
    """
    
    @staticmethod
    def capture_current_configuration(
        db: Session,
        org_id: int,
        component_name: str,
        component_type: Optional[str] = None,
        include_metadata: bool = True,
    ) -> Dict:
        """
        Capture current configuration for a component (CM-2).
        
        This method collects configuration from various sources:
        - Database settings
        - Application configuration
        - Environment variables (non-sensitive)
        - Service configurations
        
        Args:
            db: Database session
            org_id: Organization ID
            component_name: Name of the component (e.g., "database", "api_server")
            component_type: Type of component (e.g., "service", "database")
            include_metadata: Whether to include metadata (timestamps, versions)
            
        Returns:
            Dictionary containing current configuration
        """
        config = {
            "component_name": component_name,
            "component_type": component_type,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Capture component-specific configuration
        if component_name == "database":
            config.update(ConfigurationBaselineService._capture_database_config(db, org_id))
        elif component_name == "api_server":
            config.update(ConfigurationBaselineService._capture_api_config(org_id))
        elif component_name == "authentication":
            config.update(ConfigurationBaselineService._capture_auth_config(org_id))
        elif component_name == "security":
            config.update(ConfigurationBaselineService._capture_security_config(org_id))
        else:
            # Generic configuration capture
            config["configuration"] = ConfigurationBaselineService._capture_generic_config(
                component_name,
                org_id,
            )
        
        if include_metadata:
            config["metadata"] = {
                "capture_method": "automated",
                "captured_by": "system",
            }
        
        return config
    
    @staticmethod
    def compare_to_baseline(
        db: Session,
        org_id: int,
        component_name: str,
        baseline_id: Optional[str] = None,
    ) -> Dict:
        """
        Compare current configuration to baseline (CM-6).
        
        Args:
            db: Database session
            org_id: Organization ID
            component_name: Name of component to check
            baseline_id: Optional specific baseline ID (uses active if not provided)
            
        Returns:
            Dictionary with comparison results including drift details
        """
        # Get baseline
        if baseline_id:
            baseline = db.query(ConfigurationBaseline).filter(
                ConfigurationBaseline.id == baseline_id,
                ConfigurationBaseline.org_id == org_id,
            ).first()
        else:
            baseline = ConfigurationManagementService.get_active_baseline(db, org_id)
        
        if not baseline:
            return {
                "has_baseline": False,
                "drift_detected": False,
                "message": "No active baseline found",
            }
        
        # Get baseline configuration for this component
        baseline_config = baseline.configuration_snapshot.get(component_name)
        
        if not baseline_config:
            return {
                "has_baseline": True,
                "drift_detected": False,
                "message": f"Component {component_name} not in baseline",
            }
        
        # Capture current configuration
        current_config = ConfigurationBaselineService.capture_current_configuration(
            db,
            org_id,
            component_name,
        )
        
        # Compare configurations
        drift_details = ConfigurationBaselineService._detect_drift(
            baseline_config,
            current_config,
        )
        
        has_drift = len(drift_details.get("differences", [])) > 0
        
        # Determine drift severity
        drift_severity = ConfigurationBaselineService._calculate_drift_severity(
            drift_details,
        )
        
        return {
            "has_baseline": True,
            "baseline_id": str(baseline.id),
            "baseline_name": baseline.name,
            "baseline_version": baseline.version,
            "drift_detected": has_drift,
            "drift_severity": drift_severity.value if drift_severity else None,
            "drift_details": drift_details,
            "current_configuration": current_config,
            "baseline_configuration": baseline_config,
        }
    
    @staticmethod
    def check_compliance(
        db: Session,
        org_id: int,
        component_name: str,
        compliance_rules: Optional[List[Dict]] = None,
        baseline_id: Optional[str] = None,
        checked_by_user_id: Optional[int] = None,
    ) -> ConfigurationComplianceStatus:
        """
        Check configuration compliance against baseline and rules (CM-6).
        
        Args:
            db: Database session
            org_id: Organization ID
            component_name: Name of component to check
            compliance_rules: Optional list of compliance rules to check
            baseline_id: Optional specific baseline ID
            checked_by_user_id: User ID performing the check
            
        Returns:
            ConfigurationComplianceStatus record
        """
        # Compare to baseline
        comparison = ConfigurationBaselineService.compare_to_baseline(
            db,
            org_id,
            component_name,
            baseline_id,
        )
        
        # Get baseline
        if baseline_id:
            baseline = db.query(ConfigurationBaseline).filter(
                ConfigurationBaseline.id == baseline_id,
            ).first()
        else:
            baseline = ConfigurationManagementService.get_active_baseline(db, org_id)
        
        # Check compliance rules
        violations = []
        if compliance_rules:
            violations = ConfigurationBaselineService._check_compliance_rules(
                comparison.get("current_configuration", {}),
                compliance_rules,
            )
        
        # Determine overall compliance status
        has_drift = comparison.get("drift_detected", False)
        has_violations = len(violations) > 0
        
        if has_drift or has_violations:
            if has_drift and has_violations:
                compliance_status = ComplianceStatus.NON_COMPLIANT.value
            elif comparison.get("drift_severity") == "critical":
                compliance_status = ComplianceStatus.NON_COMPLIANT.value
            else:
                compliance_status = ComplianceStatus.PARTIALLY_COMPLIANT.value
        else:
            compliance_status = ComplianceStatus.COMPLIANT.value
        
        # Generate remediation suggestions
        remediation_suggestions = ConfigurationBaselineService._generate_remediation_suggestions(
            comparison,
            violations,
        )
        
        # Create or update compliance status record
        existing_status = db.query(ConfigurationComplianceStatus).filter(
            ConfigurationComplianceStatus.org_id == org_id,
            ConfigurationComplianceStatus.component_name == component_name,
            ConfigurationComplianceStatus.baseline_id == (baseline.id if baseline else None),
        ).first()
        
        if existing_status:
            # Update existing record
            existing_status.compliance_status = compliance_status
            existing_status.current_configuration = comparison.get("current_configuration")
            existing_status.expected_configuration = comparison.get("baseline_configuration")
            existing_status.has_drift = has_drift
            existing_status.drift_details = comparison.get("drift_details")
            existing_status.drift_severity = comparison.get("drift_severity")
            existing_status.compliance_rules_checked = [r.get("name") for r in (compliance_rules or [])]
            existing_status.compliance_violations = violations
            existing_status.remediation_suggestions = remediation_suggestions
            existing_status.last_checked_at = datetime.now(timezone.utc)
            existing_status.checked_by_user_id = checked_by_user_id
            existing_status.check_method = "automated"
            
            db.commit()
            db.refresh(existing_status)
            
            return existing_status
        else:
            # Create new record
            compliance_status_record = ConfigurationComplianceStatus(
                org_id=org_id,
                baseline_id=baseline.id if baseline else None,
                component_name=component_name,
                component_type=comparison.get("current_configuration", {}).get("component_type"),
                compliance_status=compliance_status,
                current_configuration=comparison.get("current_configuration"),
                expected_configuration=comparison.get("baseline_configuration"),
                has_drift=has_drift,
                drift_details=comparison.get("drift_details"),
                drift_severity=comparison.get("drift_severity"),
                compliance_rules_checked=[r.get("name") for r in (compliance_rules or [])],
                compliance_violations=violations,
                remediation_suggestions=remediation_suggestions,
                checked_by_user_id=checked_by_user_id,
                check_method="automated",
            )
            
            db.add(compliance_status_record)
            db.commit()
            db.refresh(compliance_status_record)
            
            return compliance_status_record
    
    @staticmethod
    def generate_drift_report(
        db: Session,
        org_id: int,
        baseline_id: Optional[str] = None,
        component_names: Optional[List[str]] = None,
    ) -> Dict:
        """
        Generate a comprehensive drift report (CM-6).
        
        Args:
            db: Database session
            org_id: Organization ID
            baseline_id: Optional specific baseline ID
            component_names: Optional list of components to check (checks all if None)
            
        Returns:
            Dictionary containing drift report
        """
        # Get baseline
        if baseline_id:
            baseline = db.query(ConfigurationBaseline).filter(
                ConfigurationBaseline.id == baseline_id,
                ConfigurationBaseline.org_id == org_id,
            ).first()
        else:
            baseline = ConfigurationManagementService.get_active_baseline(db, org_id)
        
        if not baseline:
            return {
                "has_baseline": False,
                "message": "No active baseline found",
                "components_checked": [],
            }
        
        # Determine components to check
        if component_names:
            components_to_check = component_names
        else:
            components_to_check = baseline.scope or []
        
        if not components_to_check:
            # Default components if scope is empty
            components_to_check = ["database", "api_server", "authentication", "security"]
        
        # Check each component
        component_results = []
        total_drift = 0
        critical_drift = 0
        
        for component_name in components_to_check:
            comparison = ConfigurationBaselineService.compare_to_baseline(
                db,
                org_id,
                component_name,
                baseline_id,
            )
            
            if comparison.get("drift_detected"):
                total_drift += 1
                if comparison.get("drift_severity") == "critical":
                    critical_drift += 1
            
            component_results.append({
                "component_name": component_name,
                "drift_detected": comparison.get("drift_detected", False),
                "drift_severity": comparison.get("drift_severity"),
                "drift_count": len(comparison.get("drift_details", {}).get("differences", [])),
            })
        
        return {
            "has_baseline": True,
            "baseline_id": str(baseline.id),
            "baseline_name": baseline.name,
            "baseline_version": baseline.version,
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "components_checked": len(components_to_check),
            "components_with_drift": total_drift,
            "components_with_critical_drift": critical_drift,
            "component_results": component_results,
        }
    
    @staticmethod
    def _capture_database_config(db: Session, org_id: int) -> Dict:
        """Capture database configuration."""
        # This is a simplified example - in production, capture actual DB config
        return {
            "database": {
                "pool_size": getattr(db.bind.pool, "size", None) if hasattr(db, "bind") else None,
                "max_overflow": getattr(db.bind.pool, "max_overflow", None) if hasattr(db, "bind") else None,
                "pool_pre_ping": True,
            },
        }
    
    @staticmethod
    def _capture_api_config(org_id: int) -> Dict:
        """Capture API server configuration."""
        from core.config import settings
        
        return {
            "api": {
                "debug": getattr(settings, "DEBUG", False),
                "cors_enabled": getattr(settings, "CORS_ENABLED", True),
                "rate_limiting_enabled": getattr(settings, "RATE_LIMITING_ENABLED", True),
            },
        }
    
    @staticmethod
    def _capture_auth_config(org_id: int) -> Dict:
        """Capture authentication configuration."""
        from core.config import settings
        
        return {
            "authentication": {
                "session_timeout_minutes": getattr(settings, "SESSION_TIMEOUT_MINUTES", 60),
                "mfa_required": getattr(settings, "MFA_REQUIRED", False),
                "password_min_length": getattr(settings, "PASSWORD_MIN_LENGTH", 12),
            },
        }
    
    @staticmethod
    def _capture_security_config(org_id: int) -> Dict:
        """Capture security configuration."""
        from core.config import settings
        
        return {
            "security": {
                "encryption_enabled": getattr(settings, "ENCRYPTION_ENABLED", True),
                "audit_logging_enabled": getattr(settings, "AUDIT_LOGGING_ENABLED", True),
                "fips_mode": getattr(settings, "FIPS_MODE", False),
            },
        }
    
    @staticmethod
    def _capture_generic_config(component_name: str, org_id: int) -> Dict:
        """Capture generic configuration for unknown components."""
        return {
            "component": component_name,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
    
    @staticmethod
    def _detect_drift(baseline_config: Dict, current_config: Dict) -> Dict:
        """
        Detect configuration drift between baseline and current.
        
        Returns dictionary with differences and drift details.
        """
        differences = []
        
        def compare_dicts(baseline: Dict, current: Dict, path: str = ""):
            """Recursively compare dictionaries."""
            all_keys = set(baseline.keys()) | set(current.keys())
            
            for key in all_keys:
                current_path = f"{path}.{key}" if path else key
                
                if key not in baseline:
                    differences.append({
                        "path": current_path,
                        "type": "added",
                        "baseline_value": None,
                        "current_value": current[key],
                    })
                elif key not in current:
                    differences.append({
                        "path": current_path,
                        "type": "removed",
                        "baseline_value": baseline[key],
                        "current_value": None,
                    })
                elif isinstance(baseline[key], dict) and isinstance(current[key], dict):
                    compare_dicts(baseline[key], current[key], current_path)
                elif baseline[key] != current[key]:
                    differences.append({
                        "path": current_path,
                        "type": "modified",
                        "baseline_value": baseline[key],
                        "current_value": current[key],
                    })
        
        compare_dicts(baseline_config, current_config)
        
        return {
            "differences": differences,
            "difference_count": len(differences),
        }
    
    @staticmethod
    def _calculate_drift_severity(drift_details: Dict) -> Optional[DriftSeverity]:
        """Calculate severity of configuration drift."""
        differences = drift_details.get("differences", [])
        
        if not differences:
            return None
        
        # Check for critical paths
        critical_paths = ["security", "authentication", "encryption", "audit"]
        
        for diff in differences:
            path = diff.get("path", "").lower()
            if any(critical in path for critical in critical_paths):
                return DriftSeverity.CRITICAL
        
        # Check difference count
        if len(differences) > 10:
            return DriftSeverity.HIGH
        elif len(differences) > 5:
            return DriftSeverity.MEDIUM
        else:
            return DriftSeverity.LOW
    
    @staticmethod
    def _check_compliance_rules(
        current_config: Dict,
        compliance_rules: List[Dict],
    ) -> List[Dict]:
        """Check configuration against compliance rules."""
        violations = []
        
        for rule in compliance_rules:
            rule_name = rule.get("name")
            rule_path = rule.get("path")
            expected_value = rule.get("expected_value")
            rule_type = rule.get("type", "equals")  # equals, contains, min, max, etc.
            
            # Navigate to config value
            config_value = current_config
            for part in rule_path.split("."):
                if isinstance(config_value, dict):
                    config_value = config_value.get(part)
                else:
                    config_value = None
                    break
            
            # Check rule
            violation = None
            if rule_type == "equals" and config_value != expected_value:
                violation = {
                    "rule_name": rule_name,
                    "path": rule_path,
                    "expected": expected_value,
                    "actual": config_value,
                }
            elif rule_type == "min" and isinstance(config_value, (int, float)) and config_value < expected_value:
                violation = {
                    "rule_name": rule_name,
                    "path": rule_path,
                    "expected_min": expected_value,
                    "actual": config_value,
                }
            elif rule_type == "max" and isinstance(config_value, (int, float)) and config_value > expected_value:
                violation = {
                    "rule_name": rule_name,
                    "path": rule_path,
                    "expected_max": expected_value,
                    "actual": config_value,
                }
            
            if violation:
                violations.append(violation)
        
        return violations
    
    @staticmethod
    def _generate_remediation_suggestions(
        comparison: Dict,
        violations: List[Dict],
    ) -> List[Dict]:
        """Generate remediation suggestions for drift and violations."""
        suggestions = []
        
        # Suggestions for drift
        drift_details = comparison.get("drift_details", {})
        differences = drift_details.get("differences", [])
        
        for diff in differences:
            if diff.get("type") == "modified":
                suggestions.append({
                    "type": "drift_correction",
                    "path": diff.get("path"),
                    "action": "restore_baseline_value",
                    "description": f"Restore {diff.get('path')} to baseline value",
                    "baseline_value": diff.get("baseline_value"),
                    "current_value": diff.get("current_value"),
                })
            elif diff.get("type") == "removed":
                suggestions.append({
                    "type": "drift_correction",
                    "path": diff.get("path"),
                    "action": "restore_setting",
                    "description": f"Restore removed setting {diff.get('path')}",
                    "baseline_value": diff.get("baseline_value"),
                })
        
        # Suggestions for violations
        for violation in violations:
            suggestions.append({
                "type": "compliance_violation",
                "path": violation.get("path"),
                "action": "fix_violation",
                "description": f"Fix compliance violation: {violation.get('rule_name')}",
                "expected": violation.get("expected") or violation.get("expected_min") or violation.get("expected_max"),
                "actual": violation.get("actual"),
            })
        
        return suggestions
