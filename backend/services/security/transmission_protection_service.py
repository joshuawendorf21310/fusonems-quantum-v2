"""
Transmission Confidentiality & Integrity Service for FedRAMP SC-8(1) compliance.

This module provides:
- TLS 1.3 enforcement
- Certificate management and validation
- Cipher suite validation
- Transmission security monitoring
- Connection security verification

FedRAMP SC-8(1): Protect the confidentiality and integrity of transmitted information
using cryptographic mechanisms.
"""

import ssl
import socket
import logging
import hashlib
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.orm import Session

from core.database import Base
from core.crypto import is_fips_enabled

logger = logging.getLogger(__name__)


class TLSVersion(Enum):
    """Supported TLS versions."""
    TLS_1_3 = "TLSv1.3"
    TLS_1_2 = "TLSv1.2"
    TLS_1_1 = "TLSv1.1"
    TLS_1_0 = "TLSv1.0"
    SSL_3_0 = "SSLv3"


class ConnectionSecurityLevel(Enum):
    """Connection security level."""
    SECURE = "secure"
    WARNING = "warning"
    INSECURE = "insecure"
    BLOCKED = "blocked"


@dataclass
class CertificateInfo:
    """Certificate information."""
    subject: str
    issuer: str
    serial_number: str
    not_before: datetime
    not_after: datetime
    fingerprint: str
    algorithm: str
    key_size: int
    is_valid: bool
    is_expired: bool
    days_until_expiry: int


class TransmissionSecurityEvent(Base):
    """Database model for transmission security events."""
    __tablename__ = "transmission_security_events"
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False, index=True)
    connection_id = Column(String(64), nullable=False, index=True)
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    destination_port = Column(Integer, nullable=True)
    tls_version = Column(String(20), nullable=True)
    cipher_suite = Column(String(100), nullable=True)
    certificate_fingerprint = Column(String(64), nullable=True)
    security_level = Column(String(20), nullable=False)
    is_blocked = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class TLSCertificate(Base):
    """Database model for TLS certificates."""
    __tablename__ = "tls_certificates"
    
    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), nullable=False, index=True)
    port = Column(Integer, nullable=False, default=443)
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    subject = Column(Text, nullable=False)
    issuer = Column(Text, nullable=False)
    serial_number = Column(String(64), nullable=False)
    not_before = Column(DateTime, nullable=False)
    not_after = Column(DateTime, nullable=False, index=True)
    algorithm = Column(String(50), nullable=False)
    key_size = Column(Integer, nullable=False)
    certificate_pem = Column(Text, nullable=True)  # Stored encrypted in production
    is_valid = Column(Boolean, nullable=False, default=True)
    last_verified_at = Column(DateTime, nullable=True)
    verification_errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TransmissionProtectionService:
    """
    Service for ensuring transmission confidentiality and integrity.
    
    Features:
    - TLS 1.3 enforcement
    - Certificate validation and management
    - Cipher suite validation
    - Connection security monitoring
    """
    
    # Approved cipher suites (TLS 1.3)
    TLS_1_3_CIPHERS = [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256",
    ]
    
    # Approved cipher suites (TLS 1.2)
    TLS_1_2_CIPHERS = [
        "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES128-GCM-SHA256",
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-ECDSA-AES128-GCM-SHA256",
        "DHE-RSA-AES256-GCM-SHA384",
        "DHE-RSA-AES128-GCM-SHA256",
    ]
    
    # Minimum TLS version (TLS 1.2)
    MIN_TLS_VERSION = ssl.TLSVersion.TLSv1_2
    
    # Preferred TLS version (TLS 1.3)
    PREFERRED_TLS_VERSION = ssl.TLSVersion.TLSv1_3
    
    def __init__(self, db: Session):
        """
        Initialize transmission protection service.
        
        Args:
            db: Database session
        """
        self.db = db
        self._require_tls_1_3 = True  # Enforce TLS 1.3 by default
        self._fips_enabled = is_fips_enabled()
    
    def verify_tls_connection(
        self,
        hostname: str,
        port: int = 443,
        timeout: int = 10,
        require_tls_1_3: Optional[bool] = None
    ) -> Tuple[ConnectionSecurityLevel, Optional[CertificateInfo], Optional[str]]:
        """
        Verify TLS connection security.
        
        Args:
            hostname: Target hostname
            port: Target port (default 443)
            timeout: Connection timeout in seconds
            require_tls_1_3: Whether to require TLS 1.3 (defaults to service setting)
            
        Returns:
            Tuple of (security_level, certificate_info, error_message)
        """
        require_tls_1_3 = require_tls_1_3 if require_tls_1_3 is not None else self._require_tls_1_3
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Set minimum TLS version
            context.minimum_version = self.MIN_TLS_VERSION
            
            # Set preferred TLS version
            if hasattr(ssl, 'TLSVersion'):
                context.maximum_version = self.PREFERRED_TLS_VERSION
            
            # Set cipher suites
            if require_tls_1_3:
                # Prefer TLS 1.3 ciphers
                context.set_ciphers(':'.join(self.TLS_1_3_CIPHERS))
            else:
                # Allow TLS 1.2 and 1.3
                context.set_ciphers(':'.join(self.TLS_1_2_CIPHERS + self.TLS_1_3_CIPHERS))
            
            # Verify certificates
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Create socket and wrap with SSL
            sock = socket.create_connection((hostname, port), timeout=timeout)
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get connection info
                tls_version = ssock.version()
                cipher_suite = ssock.cipher()
                cert = ssock.getpeercert(binary_form=False)
                cert_binary = ssock.getpeercert(binary_form=True)
                
                # Parse certificate
                cert_info = self._parse_certificate(cert, cert_binary)
                
                # Verify TLS version
                if require_tls_1_3 and tls_version != "TLSv1.3":
                    return (
                        ConnectionSecurityLevel.INSECURE,
                        cert_info,
                        f"TLS 1.3 required, but connection uses {tls_version}"
                    )
                
                # Verify cipher suite
                if cipher_suite:
                    cipher_name = cipher_suite[0]
                    if require_tls_1_3:
                        if cipher_name not in self.TLS_1_3_CIPHERS:
                            return (
                                ConnectionSecurityLevel.WARNING,
                                cert_info,
                                f"Cipher suite {cipher_name} not in approved TLS 1.3 list"
                            )
                    else:
                        if cipher_name not in (self.TLS_1_2_CIPHERS + self.TLS_1_3_CIPHERS):
                            return (
                                ConnectionSecurityLevel.WARNING,
                                cert_info,
                                f"Cipher suite {cipher_name} not in approved list"
                            )
                
                # Verify certificate
                if not cert_info.is_valid:
                    return (
                        ConnectionSecurityLevel.INSECURE,
                        cert_info,
                        "Certificate validation failed"
                    )
                
                if cert_info.is_expired:
                    return (
                        ConnectionSecurityLevel.INSECURE,
                        cert_info,
                        f"Certificate expired {cert_info.days_until_expiry} days ago"
                    )
                
                # Check certificate expiry warning (30 days)
                if cert_info.days_until_expiry < 30:
                    return (
                        ConnectionSecurityLevel.WARNING,
                        cert_info,
                        f"Certificate expires in {cert_info.days_until_expiry} days"
                    )
                
                # Store certificate in database
                self._store_certificate(hostname, port, cert_info, cert_binary)
                
                # Log secure connection
                self._log_security_event(
                    event_type="tls_verification",
                    connection_id=f"{hostname}:{port}",
                    source_ip=None,
                    destination_ip=hostname,
                    destination_port=port,
                    tls_version=tls_version,
                    cipher_suite=cipher_name if cipher_suite else None,
                    certificate_fingerprint=cert_info.fingerprint,
                    security_level=ConnectionSecurityLevel.SECURE.value,
                    is_blocked=False
                )
                
                return (ConnectionSecurityLevel.SECURE, cert_info, None)
        
        except ssl.SSLError as e:
            error_msg = f"SSL error: {str(e)}"
            logger.warning(f"TLS verification failed for {hostname}:{port}: {error_msg}")
            
            self._log_security_event(
                event_type="tls_verification_failed",
                connection_id=f"{hostname}:{port}",
                source_ip=None,
                destination_ip=hostname,
                destination_port=port,
                tls_version=None,
                cipher_suite=None,
                certificate_fingerprint=None,
                security_level=ConnectionSecurityLevel.INSECURE.value,
                is_blocked=True,
                error_message=error_msg
            )
            
            return (ConnectionSecurityLevel.INSECURE, None, error_msg)
        
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"TLS verification error for {hostname}:{port}: {error_msg}")
            
            return (ConnectionSecurityLevel.INSECURE, None, error_msg)
    
    def _parse_certificate(self, cert: Dict, cert_binary: bytes) -> CertificateInfo:
        """
        Parse certificate information.
        
        Args:
            cert: Certificate dictionary from SSL
            cert_binary: Binary certificate data
            
        Returns:
            CertificateInfo object
        """
        # Calculate fingerprint
        fingerprint = hashlib.sha256(cert_binary).hexdigest()
        
        # Parse dates
        not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        
        # Check expiry
        now = datetime.utcnow()
        is_expired = now > not_after
        days_until_expiry = (not_after - now).days if not is_expired else (now - not_after).days
        
        # Extract subject and issuer
        subject = self._format_name(cert.get('subject', []))
        issuer = self._format_name(cert.get('issuer', []))
        
        # Extract algorithm and key size
        algorithm = cert.get('signatureAlgorithm', {}).get('algorithm', 'unknown')
        key_size = self._extract_key_size(cert)
        
        return CertificateInfo(
            subject=subject,
            issuer=issuer,
            serial_number=str(cert.get('serialNumber', '')),
            not_before=not_before,
            not_after=not_after,
            fingerprint=fingerprint,
            algorithm=algorithm,
            key_size=key_size,
            is_valid=True,  # SSL library already validated
            is_expired=is_expired,
            days_until_expiry=days_until_expiry
        )
    
    def _format_name(self, name_list: List) -> str:
        """Format certificate name list to string."""
        parts = []
        for item in name_list:
            if isinstance(item, tuple):
                for key, value in item:
                    parts.append(f"{key}={value}")
        return ", ".join(parts)
    
    def _extract_key_size(self, cert: Dict) -> int:
        """Extract key size from certificate."""
        # Try to get from public key info
        public_key_info = cert.get('subjectPublicKeyInfo', {})
        if public_key_info:
            # This is simplified - actual extraction would parse ASN.1
            return 2048  # Default assumption
        
        return 2048  # Default
    
    def _store_certificate(
        self,
        hostname: str,
        port: int,
        cert_info: CertificateInfo,
        cert_binary: bytes
    ) -> None:
        """Store certificate in database."""
        # Check if certificate already exists
        existing = self.db.query(TLSCertificate).filter(
            TLSCertificate.fingerprint == cert_info.fingerprint
        ).first()
        
        if existing:
            # Update existing record
            existing.hostname = hostname
            existing.port = port
            existing.last_verified_at = datetime.utcnow()
            existing.is_valid = cert_info.is_valid and not cert_info.is_expired
            existing.updated_at = datetime.utcnow()
        else:
            # Create new record
            # Note: In production, certificate_pem should be encrypted
            cert_pem = None  # Store encrypted in production
            
            new_cert = TLSCertificate(
                hostname=hostname,
                port=port,
                fingerprint=cert_info.fingerprint,
                subject=cert_info.subject,
                issuer=cert_info.issuer,
                serial_number=cert_info.serial_number,
                not_before=cert_info.not_before,
                not_after=cert_info.not_after,
                algorithm=cert_info.algorithm,
                key_size=cert_info.key_size,
                certificate_pem=cert_pem,
                is_valid=cert_info.is_valid and not cert_info.is_expired,
                last_verified_at=datetime.utcnow()
            )
            self.db.add(new_cert)
        
        self.db.commit()
    
    def _log_security_event(
        self,
        event_type: str,
        connection_id: str,
        source_ip: Optional[str],
        destination_ip: Optional[str],
        destination_port: Optional[int],
        tls_version: Optional[str],
        cipher_suite: Optional[str],
        certificate_fingerprint: Optional[str],
        security_level: str,
        is_blocked: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Log transmission security event."""
        event = TransmissionSecurityEvent(
            event_type=event_type,
            connection_id=connection_id,
            source_ip=source_ip,
            destination_ip=destination_ip,
            destination_port=destination_port,
            tls_version=tls_version,
            cipher_suite=cipher_suite,
            certificate_fingerprint=certificate_fingerprint,
            security_level=security_level,
            is_blocked=is_blocked,
            error_message=error_message,
            metadata=metadata or {}
        )
        self.db.add(event)
        self.db.commit()
    
    def check_certificate_expiry(self, days_ahead: int = 30) -> List[TLSCertificate]:
        """
        Check for certificates expiring within specified days.
        
        Args:
            days_ahead: Number of days to check ahead
            
        Returns:
            List of certificates expiring soon
        """
        expiry_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        expiring = self.db.query(TLSCertificate).filter(
            TLSCertificate.not_after <= expiry_date,
            TLSCertificate.is_valid == True
        ).all()
        
        return expiring
    
    def get_connection_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get transmission security statistics.
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary with statistics
        """
        query = self.db.query(TransmissionSecurityEvent)
        
        if start_date:
            query = query.filter(TransmissionSecurityEvent.created_at >= start_date)
        if end_date:
            query = query.filter(TransmissionSecurityEvent.created_at <= end_date)
        
        total_events = query.count()
        secure_events = query.filter(
            TransmissionSecurityEvent.security_level == ConnectionSecurityLevel.SECURE.value
        ).count()
        insecure_events = query.filter(
            TransmissionSecurityEvent.security_level == ConnectionSecurityLevel.INSECURE.value
        ).count()
        blocked_events = query.filter(
            TransmissionSecurityEvent.is_blocked == True
        ).count()
        
        return {
            "total_events": total_events,
            "secure_connections": secure_events,
            "insecure_connections": insecure_events,
            "blocked_connections": blocked_events,
            "security_rate": (secure_events / total_events * 100) if total_events > 0 else 0,
            "fips_enabled": self._fips_enabled
        }
    
    def validate_cipher_suite(self, cipher_suite: str, tls_version: str) -> bool:
        """
        Validate cipher suite against approved list.
        
        Args:
            cipher_suite: Cipher suite name
            tls_version: TLS version
            
        Returns:
            True if cipher suite is approved
        """
        if tls_version == "TLSv1.3":
            return cipher_suite in self.TLS_1_3_CIPHERS
        elif tls_version == "TLSv1.2":
            return cipher_suite in self.TLS_1_2_CIPHERS
        else:
            return False
