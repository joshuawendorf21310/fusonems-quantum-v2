"""
Public Key Infrastructure Service for FedRAMP SC-17 compliance.

This module provides:
- Certificate lifecycle management
- Certificate revocation (CRL/OCSP checking)
- Certificate validation
- Key pair generation and management
- Certificate signing request (CSR) handling

FedRAMP SC-17: Employ public key infrastructure certificates.
"""

import ssl
import logging
import hashlib
import base64
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.x509.ocsp import OCSPRequestBuilder, OCSPResponseStatus
from cryptography.hazmat.backends import default_backend

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.orm import Session

from core.database import Base
from core.crypto import is_fips_enabled, generate_key

logger = logging.getLogger(__name__)


class CertificateStatus(Enum):
    """Certificate status."""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    SUSPENDED = "suspended"


class CertificateType(Enum):
    """Certificate type."""
    SSL_TLS = "ssl_tls"
    CODE_SIGNING = "code_signing"
    EMAIL = "email"
    CLIENT_AUTH = "client_auth"
    SERVER_AUTH = "server_auth"


class KeyAlgorithm(Enum):
    """Key algorithm."""
    RSA = "rsa"
    ECDSA = "ecdsa"
    ED25519 = "ed25519"


class PKICertificate(Base):
    """Database model for PKI certificates."""
    __tablename__ = "pki_certificates"
    
    id = Column(Integer, primary_key=True)
    certificate_id = Column(String(64), unique=True, nullable=False, index=True)
    certificate_type = Column(String(50), nullable=False, index=True)
    
    # Certificate details
    subject = Column(Text, nullable=False)
    issuer = Column(Text, nullable=False)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    fingerprint_sha256 = Column(String(64), unique=True, nullable=False, index=True)
    fingerprint_sha1 = Column(String(40), nullable=True)
    
    # Validity
    not_before = Column(DateTime, nullable=False)
    not_after = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), nullable=False, default=CertificateStatus.VALID.value, index=True)
    
    # Key information
    key_algorithm = Column(String(20), nullable=False)
    key_size = Column(Integer, nullable=False)
    public_key_pem = Column(Text, nullable=True)  # Stored encrypted in production
    
    # Certificate data
    certificate_pem = Column(Text, nullable=False)  # Stored encrypted in production
    certificate_chain_pem = Column(Text, nullable=True)  # Stored encrypted in production
    
    # Revocation
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(50), nullable=True)
    crl_url = Column(String(500), nullable=True)
    ocsp_url = Column(String(500), nullable=True)
    
    # Validation
    last_validated_at = Column(DateTime, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    ocsp_response = Column(JSON, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CertificateRevocationList(Base):
    """Database model for Certificate Revocation Lists."""
    __tablename__ = "certificate_revocation_lists"
    
    id = Column(Integer, primary_key=True)
    crl_id = Column(String(64), unique=True, nullable=False, index=True)
    issuer = Column(Text, nullable=False, index=True)
    crl_url = Column(String(500), nullable=False)
    
    # CRL data
    crl_number = Column(String(64), nullable=True)
    this_update = Column(DateTime, nullable=False)
    next_update = Column(DateTime, nullable=False, index=True)
    
    # Revoked certificates
    revoked_serials = Column(JSON, nullable=True)  # List of revoked serial numbers
    
    # Metadata
    last_fetched_at = Column(DateTime, nullable=True)
    fetch_errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class PKIService:
    """
    Service for Public Key Infrastructure management.
    
    Features:
    - Certificate lifecycle management
    - CRL checking
    - OCSP checking
    - Certificate validation
    - Key pair generation
    """
    
    def __init__(self, db: Session):
        """
        Initialize PKI service.
        
        Args:
            db: Database session
        """
        self.db = db
        self._fips_enabled = is_fips_enabled()
    
    def generate_key_pair(
        self,
        algorithm: KeyAlgorithm = KeyAlgorithm.RSA,
        key_size: int = 2048,
        curve: Optional[str] = None
    ) -> Tuple[bytes, bytes]:
        """
        Generate key pair.
        
        Args:
            algorithm: Key algorithm (RSA, ECDSA, ED25519)
            key_size: Key size in bits (for RSA)
            curve: Curve name (for ECDSA, e.g., "secp256r1")
            
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        if algorithm == KeyAlgorithm.RSA:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
        elif algorithm == KeyAlgorithm.ECDSA:
            if curve == "secp256r1":
                from cryptography.hazmat.primitives.asymmetric import ec
                private_key = ec.generate_private_key(
                    ec.SECP256R1(),
                    backend=default_backend()
                )
            elif curve == "secp384r1":
                private_key = ec.generate_private_key(
                    ec.SECP384R1(),
                    backend=default_backend()
                )
            else:
                raise ValueError(f"Unsupported curve: {curve}")
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Serialize keys
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_key_pem, public_key_pem
    
    def store_certificate(
        self,
        certificate_pem: str,
        certificate_type: CertificateType = CertificateType.SSL_TLS,
        certificate_chain_pem: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> PKICertificate:
        """
        Store certificate in database.
        
        Args:
            certificate_pem: Certificate PEM string
            certificate_type: Certificate type
            certificate_chain_pem: Optional certificate chain PEM
            metadata: Optional metadata
            
        Returns:
            PKICertificate object
        """
        # Parse certificate
        cert = x509.load_pem_x509_certificate(
            certificate_pem.encode('utf-8'),
            backend=default_backend()
        )
        
        # Extract information
        subject = self._format_name(cert.subject)
        issuer = self._format_name(cert.issuer)
        serial_number = str(cert.serial_number)
        
        # Calculate fingerprints
        fingerprint_sha256 = hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest()
        fingerprint_sha1 = hashlib.sha1(cert.public_bytes(serialization.Encoding.DER)).hexdigest()
        
        # Extract key information
        public_key = cert.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            key_algorithm = KeyAlgorithm.RSA.value
            key_size = public_key.key_size
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            key_algorithm = KeyAlgorithm.ECDSA.value
            key_size = public_key.curve.key_size
        else:
            key_algorithm = "unknown"
            key_size = 0
        
        # Extract validity dates
        not_before = cert.not_valid_before
        not_after = cert.not_valid_after
        
        # Extract OCSP and CRL URLs
        ocsp_url = None
        crl_url = None
        
        try:
            for ext in cert.extensions:
                if ext.oid == x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS:
                    for access_desc in ext.value:
                        if access_desc.access_method == x509.oid.AuthorityInformationAccessOID.OCSP:
                            ocsp_url = access_desc.access_location.value
                        elif access_desc.access_method == x509.oid.AuthorityInformationAccessOID.CA_ISSUERS:
                            pass  # CA issuer URL
                
                elif ext.oid == x509.oid.ExtensionOID.CRL_DISTRIBUTION_POINTS:
                    for dist_point in ext.value:
                        if dist_point.full_name:
                            for name in dist_point.full_name:
                                crl_url = name.value
                                break
        except Exception as e:
            logger.warning(f"Error extracting certificate extensions: {e}")
        
        # Check if certificate already exists
        existing = self.db.query(PKICertificate).filter(
            PKICertificate.fingerprint_sha256 == fingerprint_sha256
        ).first()
        
        if existing:
            # Update existing certificate
            existing.certificate_pem = certificate_pem
            existing.certificate_chain_pem = certificate_chain_pem
            existing.not_before = not_before
            existing.not_after = not_after
            existing.status = self._determine_status(not_after)
            existing.ocsp_url = ocsp_url
            existing.crl_url = crl_url
            existing.updated_at = datetime.utcnow()
            if metadata:
                existing.metadata = metadata
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new certificate record
        cert_record = PKICertificate(
            certificate_id=self._generate_certificate_id(),
            certificate_type=certificate_type.value,
            subject=subject,
            issuer=issuer,
            serial_number=serial_number,
            fingerprint_sha256=fingerprint_sha256,
            fingerprint_sha1=fingerprint_sha1,
            not_before=not_before,
            not_after=not_after,
            status=self._determine_status(not_after),
            key_algorithm=key_algorithm,
            key_size=key_size,
            certificate_pem=certificate_pem,  # In production, encrypt this
            certificate_chain_pem=certificate_chain_pem,  # In production, encrypt this
            ocsp_url=ocsp_url,
            crl_url=crl_url,
            metadata=metadata or {}
        )
        
        self.db.add(cert_record)
        self.db.commit()
        self.db.refresh(cert_record)
        
        logger.info(f"Stored certificate: {cert_record.certificate_id}")
        return cert_record
    
    def check_certificate_revocation(
        self,
        certificate_id: str,
        use_ocsp: bool = True,
        use_crl: bool = True
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Check certificate revocation status.
        
        Args:
            certificate_id: Certificate ID
            use_ocsp: Use OCSP checking
            use_crl: Use CRL checking
            
        Returns:
            Tuple of (is_revoked, revocation_reason, ocsp_response)
        """
        cert = self.db.query(PKICertificate).filter(
            PKICertificate.certificate_id == certificate_id
        ).first()
        
        if not cert:
            raise ValueError(f"Certificate not found: {certificate_id}")
        
        # Check OCSP
        if use_ocsp and cert.ocsp_url:
            try:
                is_revoked, reason, ocsp_response = self._check_ocsp(cert)
                if is_revoked:
                    cert.status = CertificateStatus.REVOKED.value
                    cert.revoked_at = datetime.utcnow()
                    cert.revocation_reason = reason
                    cert.ocsp_response = ocsp_response
                    self.db.commit()
                    return True, reason, ocsp_response
            except Exception as e:
                logger.warning(f"OCSP check failed for {certificate_id}: {e}")
        
        # Check CRL
        if use_crl and cert.crl_url:
            try:
                is_revoked, reason = self._check_crl(cert)
                if is_revoked:
                    cert.status = CertificateStatus.REVOKED.value
                    cert.revoked_at = datetime.utcnow()
                    cert.revocation_reason = reason
                    self.db.commit()
                    return True, reason, None
            except Exception as e:
                logger.warning(f"CRL check failed for {certificate_id}: {e}")
        
        return False, None, None
    
    def _check_ocsp(
        self,
        cert: PKICertificate
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Check certificate revocation via OCSP.
        
        Args:
            cert: Certificate record
            
        Returns:
            Tuple of (is_revoked, revocation_reason, ocsp_response)
        """
        # Parse certificate
        cert_obj = x509.load_pem_x509_certificate(
            cert.certificate_pem.encode('utf-8'),
            backend=default_backend()
        )
        
        # Build OCSP request
        builder = OCSPRequestBuilder()
        builder = builder.add_certificate(
            cert_obj,
            cert_obj,  # Issuer cert (simplified - should fetch issuer cert)
            hashes.SHA256()
        )
        
        request = builder.build()
        
        # In production, send HTTP request to OCSP URL
        # For now, return not revoked
        logger.info(f"OCSP check for certificate {cert.certificate_id} (placeholder)")
        
        return False, None, None
    
    def _check_crl(
        self,
        cert: PKICertificate
    ) -> Tuple[bool, Optional[str]]:
        """
        Check certificate revocation via CRL.
        
        Args:
            cert: Certificate record
            
        Returns:
            Tuple of (is_revoked, revocation_reason)
        """
        # Check if CRL exists in database
        crl_record = self.db.query(CertificateRevocationList).filter(
            CertificateRevocationList.issuer == cert.issuer
        ).order_by(CertificateRevocationList.updated_at.desc()).first()
        
        if crl_record and crl_record.revoked_serials:
            if cert.serial_number in crl_record.revoked_serials:
                return True, "Revoked per CRL"
        
        # In production, fetch CRL from cert.crl_url
        # For now, return not revoked
        logger.info(f"CRL check for certificate {cert.certificate_id} (placeholder)")
        
        return False, None
    
    def validate_certificate(
        self,
        certificate_id: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate certificate.
        
        Args:
            certificate_id: Certificate ID
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        cert = self.db.query(PKICertificate).filter(
            PKICertificate.certificate_id == certificate_id
        ).first()
        
        if not cert:
            return False, [f"Certificate not found: {certificate_id}"]
        
        errors = []
        
        # Check expiry
        now = datetime.utcnow()
        if now < cert.not_before:
            errors.append("Certificate not yet valid")
        if now > cert.not_after:
            errors.append("Certificate expired")
            cert.status = CertificateStatus.EXPIRED.value
        
        # Check revocation
        if cert.status == CertificateStatus.REVOKED.value:
            errors.append("Certificate revoked")
        
        # Check key size (minimum 2048 bits for RSA)
        if cert.key_algorithm == KeyAlgorithm.RSA.value and cert.key_size < 2048:
            errors.append(f"Key size {cert.key_size} bits is below minimum 2048 bits")
        
        # Update validation timestamp
        cert.last_validated_at = now
        if errors:
            cert.validation_errors = errors
        else:
            cert.validation_errors = None
        
        self.db.commit()
        
        return len(errors) == 0, errors
    
    def get_expiring_certificates(
        self,
        days_ahead: int = 30
    ) -> List[PKICertificate]:
        """
        Get certificates expiring within specified days.
        
        Args:
            days_ahead: Number of days to check ahead
            
        Returns:
            List of expiring certificates
        """
        expiry_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        expiring = self.db.query(PKICertificate).filter(
            PKICertificate.not_after <= expiry_date,
            PKICertificate.status == CertificateStatus.VALID.value
        ).all()
        
        return expiring
    
    def revoke_certificate(
        self,
        certificate_id: str,
        reason: str
    ) -> None:
        """
        Revoke certificate.
        
        Args:
            certificate_id: Certificate ID
            reason: Revocation reason
        """
        cert = self.db.query(PKICertificate).filter(
            PKICertificate.certificate_id == certificate_id
        ).first()
        
        if cert:
            cert.status = CertificateStatus.REVOKED.value
            cert.revoked_at = datetime.utcnow()
            cert.revocation_reason = reason
            self.db.commit()
            
            logger.warning(f"Revoked certificate: {certificate_id}, reason: {reason}")
    
    def _determine_status(self, not_after: datetime) -> str:
        """Determine certificate status based on expiry."""
        if datetime.utcnow() > not_after:
            return CertificateStatus.EXPIRED.value
        return CertificateStatus.VALID.value
    
    def _format_name(self, name: x509.Name) -> str:
        """Format certificate name to string."""
        parts = []
        for attr in name:
            parts.append(f"{attr.oid._name}={attr.value}")
        return ", ".join(parts)
    
    def _generate_certificate_id(self) -> str:
        """Generate unique certificate ID."""
        import secrets
        return secrets.token_urlsafe(32)
