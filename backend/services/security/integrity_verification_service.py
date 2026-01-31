"""
Software & Information Integrity Verification Service for FedRAMP SI-7 Compliance

This service provides:
- Code signing verification
- Checksum validation
- Tamper detection

FedRAMP SI-7: Software & Information Integrity
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

from sqlalchemy.orm import Session

from models.system_integrity import (
    IntegrityVerification,
    IntegrityStatus,
    IntegrityCheckType,
)
from utils.logger import logger


class IntegrityVerificationService:
    """
    Service for software and information integrity verification.
    
    FedRAMP SI-7: Software & Information Integrity
    """
    
    def __init__(self, db: Session):
        """
        Initialize integrity verification service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def verify_file_integrity(
        self,
        file_path: str,
        expected_hash: Optional[str] = None,
        baseline_id: Optional[str] = None,
    ) -> IntegrityVerification:
        """
        Verify file integrity using checksum/hash.
        
        Args:
            file_path: Path to file to verify
            expected_hash: Expected hash value (SHA-256)
            baseline_id: Baseline identifier for comparison
            
        Returns:
            IntegrityVerification record
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Calculate actual hash
        actual_hash = self._calculate_file_hash(file_path)
        
        # Get baseline hash if baseline_id provided
        baseline_hash = None
        if baseline_id:
            baseline = self.db.query(IntegrityVerification).filter(
                IntegrityVerification.baseline_id == baseline_id
            ).first()
            if baseline:
                baseline_hash = baseline.expected_hash or baseline.actual_hash
        
        # Use expected_hash or baseline_hash
        expected = expected_hash or baseline_hash
        
        # Create verification record
        verification = IntegrityVerification(
            verification_id=f"verify_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{actual_hash[:8]}",
            check_type=IntegrityCheckType.CHECKSUM.value,
            target_type="file",
            target_name=file_path_obj.name,
            target_path=str(file_path),
            expected_hash=expected,
            actual_hash=actual_hash,
            hash_match=(actual_hash == expected) if expected else None,
            baseline_id=baseline_id,
            baseline_hash=baseline_hash,
            status=IntegrityStatus.PENDING.value,
        )
        
        self.db.add(verification)
        self.db.commit()
        
        # Perform verification
        if expected:
            verification.hash_match = (actual_hash == expected)
            verification.verification_passed = verification.hash_match
            verification.status = IntegrityStatus.VERIFIED.value if verification.hash_match else IntegrityStatus.FAILED.value
            verification.verification_message = (
                "File integrity verified" if verification.hash_match
                else "File integrity check failed - hash mismatch"
            )
            
            if not verification.hash_match:
                verification.tamper_detected = True
                verification.tamper_details = f"Hash mismatch: expected {expected[:16]}..., got {actual_hash[:16]}..."
                verification.tamper_timestamp = datetime.utcnow()
        else:
            # No expected hash - just record the hash
            verification.verification_passed = True
            verification.status = IntegrityStatus.VERIFIED.value
            verification.verification_message = "File hash calculated (no baseline for comparison)"
        
        verification.verified_at = datetime.utcnow()
        verification.verification_method = "SHA-256"
        
        self.db.commit()
        self.db.refresh(verification)
        
        logger.info(
            f"File integrity verified: {file_path}",
            extra={
                "verification_id": verification.verification_id,
                "file_path": file_path,
                "hash_match": verification.hash_match,
                "tamper_detected": verification.tamper_detected,
                "event_type": "integrity.verified",
            }
        )
        
        return verification
    
    def verify_code_signing(
        self,
        file_path: str,
    ) -> IntegrityVerification:
        """
        Verify code signing for a file.
        
        Args:
            file_path: Path to signed file
            
        Returns:
            IntegrityVerification record
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        verification = IntegrityVerification(
            verification_id=f"sign_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file_path_obj.name}",
            check_type=IntegrityCheckType.CODE_SIGNING.value,
            target_type="file",
            target_name=file_path_obj.name,
            target_path=str(file_path),
            status=IntegrityStatus.PENDING.value,
        )
        
        self.db.add(verification)
        self.db.commit()
        
        try:
            # Check for code signature (platform-specific)
            signed, signer, valid = self._check_code_signature(file_path)
            
            verification.signed = signed
            verification.signer = signer
            verification.signature_valid = valid
            verification.verification_passed = signed and valid
            verification.status = IntegrityStatus.VERIFIED.value if (signed and valid) else IntegrityStatus.FAILED.value
            verification.verification_message = (
                f"Code signing verified: {signer}" if (signed and valid)
                else "Code signing verification failed"
            )
            
            if not signed or not valid:
                verification.tamper_detected = True
                verification.tamper_details = "Code signature missing or invalid"
                verification.tamper_timestamp = datetime.utcnow()
        
        except Exception as e:
            logger.error(f"Code signing verification failed: {e}", exc_info=True)
            verification.status = IntegrityStatus.ERROR.value
            verification.verification_message = f"Verification error: {str(e)}"
        
        verification.verified_at = datetime.utcnow()
        verification.verification_method = "code_signing"
        
        self.db.commit()
        self.db.refresh(verification)
        
        return verification
    
    def create_baseline(
        self,
        file_path: str,
        baseline_id: str,
    ) -> IntegrityVerification:
        """
        Create an integrity baseline for a file.
        
        Args:
            file_path: Path to file
            baseline_id: Unique baseline identifier
            
        Returns:
            IntegrityVerification record (baseline)
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        hash_value = self._calculate_file_hash(file_path)
        
        verification = IntegrityVerification(
            verification_id=f"baseline_{baseline_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            check_type=IntegrityCheckType.CHECKSUM.value,
            target_type="file",
            target_name=file_path_obj.name,
            target_path=str(file_path),
            baseline_id=baseline_id,
            expected_hash=hash_value,
            actual_hash=hash_value,
            hash_match=True,
            verification_passed=True,
            status=IntegrityStatus.VERIFIED.value,
            verification_message=f"Baseline created: {baseline_id}",
            baseline_created_at=datetime.utcnow(),
            verified_at=datetime.utcnow(),
        )
        
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        
        logger.info(
            f"Integrity baseline created: {baseline_id}",
            extra={
                "baseline_id": baseline_id,
                "file_path": file_path,
                "event_type": "integrity.baseline.created",
            }
        )
        
        return verification
    
    def detect_tampering(
        self,
        baseline_id: str,
        file_path: str,
    ) -> IntegrityVerification:
        """
        Detect tampering by comparing against baseline.
        
        Args:
            baseline_id: Baseline identifier
            file_path: Path to file to check
            
        Returns:
            IntegrityVerification record
        """
        baseline = self.db.query(IntegrityVerification).filter(
            IntegrityVerification.baseline_id == baseline_id,
            IntegrityVerification.verification_passed == True,
        ).order_by(IntegrityVerification.baseline_created_at.desc()).first()
        
        if not baseline:
            raise ValueError(f"Baseline not found: {baseline_id}")
        
        return self.verify_file_integrity(
            file_path=file_path,
            expected_hash=baseline.expected_hash,
            baseline_id=baseline_id,
        )
    
    def get_verifications_by_status(
        self,
        status: Optional[IntegrityStatus] = None,
        tamper_detected: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[IntegrityVerification], int]:
        """
        Get verifications filtered by status and tamper detection.
        
        Args:
            status: Filter by status
            tamper_detected: Filter by tamper detection
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Tuple of (verifications list, total count)
        """
        query = self.db.query(IntegrityVerification)
        
        if status:
            query = query.filter(IntegrityVerification.status == status.value)
        
        if tamper_detected is not None:
            query = query.filter(IntegrityVerification.tamper_detected == tamper_detected)
        
        total = query.count()
        verifications = query.order_by(
            IntegrityVerification.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return verifications, total
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA-256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _check_code_signature(self, file_path: str) -> tuple[bool, Optional[str], bool]:
        """
        Check code signature for a file (platform-specific).
        
        Args:
            file_path: Path to file
            
        Returns:
            Tuple of (signed, signer, valid)
        """
        # Platform-specific code signing checks
        # Linux: Check GPG signatures
        # macOS: Check code signing with codesign
        # Windows: Check Authenticode signatures
        
        try:
            # Try codesign on macOS
            result = subprocess.run(
                ["codesign", "-dv", "--verbose=4", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode == 0:
                # Extract signer from output
                signer = None
                for line in result.stdout.split('\n'):
                    if 'Authority=' in line:
                        signer = line.split('=')[1].strip()
                        break
                
                return True, signer or "Unknown", True
        
        except FileNotFoundError:
            pass
        except Exception:
            pass
        
        # Try GPG for Linux
        try:
            result = subprocess.run(
                ["gpg", "--verify", f"{file_path}.sig", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode == 0:
                return True, "GPG", True
        
        except FileNotFoundError:
            pass
        except Exception:
            pass
        
        # No signature found
        return False, None, False
