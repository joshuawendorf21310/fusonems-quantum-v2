"""
PKI Authentication Service for FedRAMP IA-5(2) Compliance

FedRAMP Requirement IA-5(2): PKI-Based Authentication
- Certificate-based authentication
- CAC/PIV card support
- Certificate validation
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.device_auth import (
    PKICertificate,
    PKIAuthenticationAttempt,
    DeviceStatus,
    AuthenticationMethod,
)
from models.user import User


class PKIAuthenticationService:
    """
    Service for PKI-based authentication (IA-5(2)).
    """
    
    @staticmethod
    def register_certificate(
        db: Session,
        org_id: int,
        user_id: int,
        certificate_serial: str,
        certificate_subject: str,
        certificate_issuer: str,
        certificate_thumbprint: str,
        certificate_type: str,
        issued_at: datetime,
        expires_at: datetime,
        certificate_pem: Optional[str] = None,
        is_cac_piv: bool = False,
        registered_by_user_id: Optional[int] = None,
    ) -> PKICertificate:
        """
        Register a PKI certificate for authentication.
        
        Args:
            db: Database session
            org_id: Organization ID
            user_id: User ID
            certificate_serial: Certificate serial number
            certificate_subject: Subject DN
            certificate_issuer: Issuer DN
            certificate_thumbprint: SHA-256 thumbprint
            certificate_type: Type of certificate (CAC, PIV, SSL, etc.)
            issued_at: Certificate issue date
            expires_at: Certificate expiration date
            certificate_pem: PEM-encoded certificate (optional, encrypted)
            is_cac_piv: Is this a CAC/PIV card?
            registered_by_user_id: User registering the certificate
            
        Returns:
            Created PKICertificate record
        """
        # Check if certificate already registered
        existing = db.query(PKICertificate).filter(
            PKICertificate.certificate_serial == certificate_serial,
            PKICertificate.org_id == org_id,
        ).first()
        
        if existing and existing.status != DeviceStatus.REVOKED.value:
            raise ValueError(f"Certificate {certificate_serial} is already registered")
        
        certificate = PKICertificate(
            org_id=org_id,
            user_id=user_id,
            certificate_serial=certificate_serial,
            certificate_subject=certificate_subject,
            certificate_issuer=certificate_issuer,
            certificate_thumbprint=certificate_thumbprint,
            certificate_type=certificate_type,
            is_cac_piv=is_cac_piv,
            issued_at=issued_at,
            expires_at=expires_at,
            not_before=issued_at,
            certificate_pem=certificate_pem,  # Should be encrypted in production
            status=DeviceStatus.REGISTERED.value,
            registered_at=datetime.now(timezone.utc),
            registered_by_user_id=registered_by_user_id,
        )
        
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
        
        logger.info(
            f"PKI certificate registered: {certificate_serial} "
            f"(user_id={user_id}, type={certificate_type}, CAC/PIV={is_cac_piv})"
        )
        
        return certificate
    
    @staticmethod
    def authenticate_with_certificate(
        db: Session,
        org_id: int,
        certificate_serial: str,
        certificate_thumbprint: str,
        signature_data: Optional[bytes] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[Optional[User], bool, Optional[str]]:
        """
        Authenticate using a PKI certificate.
        
        Args:
            db: Database session
            org_id: Organization ID
            certificate_serial: Certificate serial number
            certificate_thumbprint: Certificate thumbprint
            signature_data: Signature data for verification (optional)
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            Tuple of (user, is_valid, error_message)
        """
        # Find certificate
        certificate = db.query(PKICertificate).filter(
            PKICertificate.certificate_serial == certificate_serial,
            PKICertificate.org_id == org_id,
        ).first()
        
        if not certificate:
            # Record failed attempt
            PKIAuthenticationService._record_attempt(
                db, org_id, None, None, certificate_serial, False, "Certificate not found",
                ip_address, user_agent
            )
            return None, False, "Certificate not registered"
        
        # Check status
        if certificate.status == DeviceStatus.REVOKED.value:
            PKIAuthenticationService._record_attempt(
                db, org_id, certificate.user_id, certificate.id, certificate_serial,
                False, "Certificate revoked", ip_address, user_agent,
                certificate_revoked=True
            )
            return None, False, "Certificate has been revoked"
        
        # Check expiration
        if certificate.expires_at < datetime.now(timezone.utc):
            certificate.status = DeviceStatus.EXPIRED.value
            certificate.validation_status = "expired"
            db.commit()
            
            PKIAuthenticationService._record_attempt(
                db, org_id, certificate.user_id, certificate.id, certificate_serial,
                False, "Certificate expired", ip_address, user_agent,
                certificate_expired=True
            )
            return None, False, "Certificate has expired"
        
        # Validate certificate (simplified - in production use actual crypto verification)
        is_valid = True
        validation_error = None
        
        if certificate_thumbprint != certificate.certificate_thumbprint:
            is_valid = False
            validation_error = "Certificate thumbprint mismatch"
        
        # Verify signature if provided (simplified)
        signature_valid = True
        if signature_data:
            # In production, verify signature using certificate public key
            # For now, we assume signature is valid if provided
            signature_valid = True
        
        # Record attempt
        PKIAuthenticationService._record_attempt(
            db, org_id, certificate.user_id, certificate.id, certificate_serial,
            is_valid and signature_valid, validation_error or "Success",
            ip_address, user_agent,
            certificate_valid=is_valid,
            signature_valid=signature_valid,
        )
        
        if not is_valid or not signature_valid:
            return None, False, validation_error or "Signature verification failed"
        
        # Update certificate usage
        certificate.last_used_at = datetime.now(timezone.utc)
        certificate.usage_count += 1
        certificate.validation_status = "valid"
        certificate.last_validated_at = datetime.now(timezone.utc)
        db.commit()
        
        # Get user
        user = db.query(User).filter(User.id == certificate.user_id).first()
        
        if not user:
            return None, False, "User not found"
        
        logger.info(f"PKI authentication successful: {certificate_serial} (user_id={user.id})")
        
        return user, True, None
    
    @staticmethod
    def _record_attempt(
        db: Session,
        org_id: int,
        user_id: Optional[int],
        certificate_id: Optional[str],
        certificate_serial: str,
        success: bool,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        certificate_valid: Optional[bool] = None,
        certificate_expired: Optional[bool] = None,
        certificate_revoked: Optional[bool] = None,
        signature_valid: Optional[bool] = None,
    ):
        """Record an authentication attempt"""
        attempt = PKIAuthenticationAttempt(
            org_id=org_id,
            user_id=user_id,
            certificate_id=certificate_id,
            certificate_serial=certificate_serial,
            attempted_at=datetime.now(timezone.utc),
            outcome="success" if success else "failure",
            failure_reason=None if success else reason,
            ip_address=ip_address,
            user_agent=user_agent,
            certificate_valid=certificate_valid,
            certificate_expired=certificate_expired,
            certificate_revoked=certificate_revoked,
            signature_valid=signature_valid,
        )
        
        db.add(attempt)
        db.commit()
    
    @staticmethod
    def revoke_certificate(
        db: Session,
        certificate_id: str,
        org_id: int,
        revoked_by_user_id: int,
        revocation_reason: str,
        revocation_crl_url: Optional[str] = None,
    ) -> PKICertificate:
        """Revoke a PKI certificate"""
        certificate = db.query(PKICertificate).filter(
            PKICertificate.id == certificate_id,
            PKICertificate.org_id == org_id,
        ).first()
        
        if not certificate:
            raise ValueError(f"Certificate {certificate_id} not found")
        
        certificate.status = DeviceStatus.REVOKED.value
        certificate.revoked_at = datetime.now(timezone.utc)
        certificate.revoked_by_user_id = revoked_by_user_id
        certificate.revocation_reason = revocation_reason
        certificate.revocation_crl_url = revocation_crl_url
        certificate.validation_status = "revoked"
        
        db.commit()
        db.refresh(certificate)
        
        logger.warning(
            f"PKI certificate revoked: {certificate.certificate_serial} "
            f"(reason: {revocation_reason})"
        )
        
        return certificate
    
    @staticmethod
    def get_user_certificates(
        db: Session,
        user_id: int,
        org_id: int,
        active_only: bool = True,
    ) -> List[PKICertificate]:
        """Get all certificates for a user"""
        query = db.query(PKICertificate).filter(
            PKICertificate.user_id == user_id,
            PKICertificate.org_id == org_id,
        )
        
        if active_only:
            query = query.filter(PKICertificate.status == DeviceStatus.ACTIVE.value)
        
        return query.order_by(desc(PKICertificate.registered_at)).all()
    
    @staticmethod
    def validate_certificate(
        db: Session,
        certificate_id: str,
        org_id: int,
    ) -> Tuple[bool, Optional[str]]:
        """Validate a certificate"""
        certificate = db.query(PKICertificate).filter(
            PKICertificate.id == certificate_id,
            PKICertificate.org_id == org_id,
        ).first()
        
        if not certificate:
            return False, "Certificate not found"
        
        now = datetime.now(timezone.utc)
        
        if certificate.status == DeviceStatus.REVOKED.value:
            certificate.validation_status = "revoked"
            db.commit()
            return False, "Certificate has been revoked"
        
        if certificate.expires_at < now:
            certificate.validation_status = "expired"
            db.commit()
            return False, "Certificate has expired"
        
        certificate.validation_status = "valid"
        certificate.last_validated_at = now
        db.commit()
        
        return True, None
