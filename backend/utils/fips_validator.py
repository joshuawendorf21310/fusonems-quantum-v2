"""
FIPS 140-2 validation utilities.

This module provides runtime validation of FIPS compliance status,
checking cryptographic module versions and FIPS mode availability.

FedRAMP SC-13: Use FIPS 140-2 validated cryptographic modules.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

try:
    import cryptography
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    import ssl
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False

from core.crypto import get_fips_mode, is_fips_enabled, CryptoBackend
from core.config import settings

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """FIPS validation result."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


class FIPSValidator:
    """Validates FIPS 140-2 compliance status."""
    
    def __init__(self):
        self._crypto_backend = CryptoBackend()
        self._validation_cache: Optional[Dict] = None
    
    def validate_fips_mode(self) -> Tuple[ValidationResult, str]:
        """
        Validate that FIPS mode is enabled if required.
        
        Returns:
            Tuple of (result, message)
        """
        fips_required = getattr(settings, "FIPS_MODE_REQUIRED", False)
        fips_enabled = is_fips_enabled()
        
        if fips_required and not fips_enabled:
            return (
                ValidationResult.FAIL,
                "FIPS mode is required but not enabled. Set FIPS_MODE_ENABLED=true or enable system FIPS mode."
            )
        
        if fips_enabled:
            return (
                ValidationResult.PASS,
                "FIPS mode is enabled and validated."
            )
        
        return (
            ValidationResult.WARNING,
            "FIPS mode is not enabled. Consider enabling for FedRAMP compliance."
        )
    
    def validate_cryptography_module(self) -> Tuple[ValidationResult, str]:
        """
        Validate cryptography module version and FIPS support.
        
        Returns:
            Tuple of (result, message)
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            return (
                ValidationResult.FAIL,
                "cryptography library is not available. Install with: pip install cryptography"
            )
        
        try:
            version = cryptography.__version__
            logger.info(f"cryptography version: {version}")
            
            # Check if backend supports FIPS
            backend = self._crypto_backend.backend
            if backend is None:
                return (
                    ValidationResult.WARNING,
                    f"cryptography {version} is available but backend initialization failed."
                )
            
            # Try to create a FIPS-approved algorithm
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                test_key = os.urandom(32)
                test_nonce = os.urandom(12)
                cipher = AESGCM(test_key)
                cipher.encrypt(test_nonce, b"test", None)
                
                return (
                    ValidationResult.PASS,
                    f"cryptography {version} supports FIPS-approved algorithms (AES-256-GCM)."
                )
            except Exception as e:
                return (
                    ValidationResult.WARNING,
                    f"cryptography {version} available but FIPS algorithms may not be fully supported: {e}"
                )
        
        except Exception as e:
            return (
                ValidationResult.FAIL,
                f"Failed to validate cryptography module: {e}"
            )
    
    def validate_openssl_version(self) -> Tuple[ValidationResult, str]:
        """
        Validate OpenSSL version (used by cryptography).
        
        Returns:
            Tuple of (result, message)
        """
        if not SSL_AVAILABLE:
            return (
                ValidationResult.WARNING,
                "SSL module not available, cannot check OpenSSL version."
            )
        
        try:
            openssl_version = ssl.OPENSSL_VERSION
            openssl_version_number = ssl.OPENSSL_VERSION_NUMBER
            
            logger.info(f"OpenSSL version: {openssl_version}")
            
            # Check for FIPS support indicators
            # Note: This is a basic check; actual FIPS validation requires
            # OpenSSL FIPS module to be compiled and enabled
            if "fips" in openssl_version.lower():
                return (
                    ValidationResult.PASS,
                    f"OpenSSL appears to have FIPS support: {openssl_version}"
                )
            
            # Check version (OpenSSL 1.0.2+ recommended for FIPS)
            version_parts = openssl_version.split()
            if len(version_parts) > 1:
                version_str = version_parts[1]
                try:
                    major, minor, patch = map(int, version_str.split(".")[:3])
                    if major >= 1 and minor >= 0:
                        return (
                            ValidationResult.PASS,
                            f"OpenSSL {version_str} is available (FIPS module may be available separately)."
                        )
                except ValueError:
                    pass
            
            return (
                ValidationResult.WARNING,
                f"OpenSSL {openssl_version} detected. Verify FIPS module is enabled if required."
            )
        
        except Exception as e:
            return (
                ValidationResult.WARNING,
                f"Could not determine OpenSSL version: {e}"
            )
    
    def validate_system_fips(self) -> Tuple[ValidationResult, str]:
        """
        Validate system-level FIPS mode.
        
        Returns:
            Tuple of (result, message)
        """
        # Check Linux FIPS mode
        fips_file = "/proc/sys/crypto/fips_enabled"
        if os.path.exists(fips_file):
            try:
                with open(fips_file, "r") as f:
                    fips_status = f.read().strip()
                    if fips_status == "1":
                        return (
                            ValidationResult.PASS,
                            "System FIPS mode is enabled (/proc/sys/crypto/fips_enabled=1)."
                        )
                    else:
                        return (
                            ValidationResult.WARNING,
                            f"System FIPS mode file exists but is not enabled ({fips_status})."
                        )
            except (IOError, OSError) as e:
                return (
                    ValidationResult.WARNING,
                    f"Could not read FIPS status file: {e}"
                )
        
        # Check environment variable
        fips_env = os.environ.get("FIPS_MODE", "").lower()
        if fips_env in ("1", "true", "enabled", "yes"):
            return (
                ValidationResult.PASS,
                "FIPS mode is enabled via FIPS_MODE environment variable."
            )
        
        return (
            ValidationResult.WARNING,
            "System FIPS mode not detected. Enable via /proc/sys/crypto/fips_enabled or FIPS_MODE env var."
        )
    
    def validate_all(self) -> Dict[str, Tuple[ValidationResult, str]]:
        """
        Run all validation checks.
        
        Returns:
            Dictionary mapping check names to (result, message) tuples
        """
        results = {
            "fips_mode": self.validate_fips_mode(),
            "cryptography_module": self.validate_cryptography_module(),
            "openssl_version": self.validate_openssl_version(),
            "system_fips": self.validate_system_fips(),
        }
        
        self._validation_cache = results
        return results
    
    def get_validation_summary(self) -> Dict:
        """
        Get a summary of validation results.
        
        Returns:
            Dictionary with summary information
        """
        if self._validation_cache is None:
            self.validate_all()
        
        results = self._validation_cache
        passed = sum(1 for r, _ in results.values() if r == ValidationResult.PASS)
        failed = sum(1 for r, _ in results.values() if r == ValidationResult.FAIL)
        warnings = sum(1 for r, _ in results.values() if r == ValidationResult.WARNING)
        
        fips_required = getattr(settings, "FIPS_MODE_REQUIRED", False)
        overall_status = "compliant" if failed == 0 and (not fips_required or is_fips_enabled()) else "non_compliant"
        
        return {
            "overall_status": overall_status,
            "fips_required": fips_required,
            "fips_enabled": is_fips_enabled(),
            "checks_passed": passed,
            "checks_failed": failed,
            "checks_warning": warnings,
            "total_checks": len(results),
            "details": {
                name: {"result": result.value, "message": message}
                for name, (result, message) in results.items()
            }
        }
    
    def log_validation_results(self) -> None:
        """Log validation results at appropriate log levels."""
        if self._validation_cache is None:
            self.validate_all()
        
        for check_name, (result, message) in self._validation_cache.items():
            if result == ValidationResult.FAIL:
                logger.error(f"FIPS validation FAIL [{check_name}]: {message}")
            elif result == ValidationResult.WARNING:
                logger.warning(f"FIPS validation WARNING [{check_name}]: {message}")
            else:
                logger.info(f"FIPS validation PASS [{check_name}]: {message}")


# Global validator instance
_validator = FIPSValidator()


def validate_fips_compliance() -> Dict:
    """
    Validate FIPS compliance and return summary.
    
    Returns:
        Validation summary dictionary
    """
    return _validator.get_validation_summary()


def log_fips_status() -> None:
    """Log FIPS compliance status."""
    _validator.log_validation_results()
