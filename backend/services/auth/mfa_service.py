"""
Multi-Factor Authentication Service
FedRAMP Control: IA-2(1), IA-2(2), IA-2(8)

Implements TOTP-based MFA for FedRAMP compliance
"""
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.user import User
from models.mfa import MFADevice, MFABackupCode
from core.config import settings
from core.logger import logger
import secrets
import hashlib


class MFAService:
    """
    Multi-Factor Authentication service implementing TOTP (RFC 6238)
    Supports hardware tokens, authenticator apps, and backup codes
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_totp_secret(self) -> str:
        """
        Generate a cryptographically secure TOTP secret
        Returns base32 encoded secret
        """
        return pyotp.random_base32()
    
    def generate_qr_code(self, user: User, secret: str) -> str:
        """
        Generate QR code for authenticator app enrollment
        Returns base64 encoded PNG image
        """
        # Generate provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=settings.BILLING_BRAND_NAME or "FusionEMS Quantum"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    def verify_totp_code(self, secret: str, code: str) -> bool:
        """
        Verify TOTP code with timing window
        Allows codes from previous, current, and next time window
        FedRAMP requires at least ±1 time window tolerance
        """
        totp = pyotp.TOTP(secret)
        # Verify with ±1 time window (90 seconds total window)
        return totp.verify(code, valid_window=1)
    
    def enroll_mfa_device(
        self,
        user: User,
        device_name: str,
        device_type: str = "totp"
    ) -> Tuple[MFADevice, str, Optional[str]]:
        """
        Enroll a new MFA device for user
        Returns (device, secret, qr_code_base64)
        """
        # Generate secret
        secret = self.generate_totp_secret()
        
        # Create device record
        device = MFADevice(
            user_id=user.id,
            org_id=user.org_id,
            device_name=device_name,
            device_type=device_type,
            secret_encrypted=self._encrypt_secret(secret),
            enrolled_at=datetime.now(timezone.utc),
            is_active=False  # Must be verified before activation
        )
        
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        
        # Generate QR code for TOTP
        qr_code = None
        if device_type == "totp":
            qr_code = self.generate_qr_code(user, secret)
        
        logger.info(f"MFA device enrolled for user {user.email}: {device_name}")
        
        return device, secret, qr_code
    
    def verify_and_activate_device(
        self,
        device: MFADevice,
        secret: str,
        verification_code: str
    ) -> bool:
        """
        Verify enrollment code and activate device
        """
        if not self.verify_totp_code(secret, verification_code):
            logger.warning(f"Failed MFA enrollment verification for device {device.id}")
            return False
        
        device.is_active = True
        device.verified_at = datetime.now(timezone.utc)
        self.db.commit()
        
        logger.info(f"MFA device activated: {device.id}")
        return True
    
    def generate_backup_codes(self, user: User, count: int = 10) -> list[str]:
        """
        Generate backup codes for account recovery
        FedRAMP requires alternative authentication methods
        """
        codes = []
        
        for _ in range(count):
            # Generate cryptographically secure 8-character code
            code = secrets.token_hex(4).upper()  # 8 hex chars
            codes.append(code)
            
            # Hash and store
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            backup_code = MFABackupCode(
                user_id=user.id,
                org_id=user.org_id,
                code_hash=code_hash,
                created_at=datetime.now(timezone.utc),
                used_at=None
            )
            self.db.add(backup_code)
        
        self.db.commit()
        
        logger.info(f"Generated {count} backup codes for user {user.email}")
        return codes
    
    def verify_backup_code(self, user: User, code: str) -> bool:
        """
        Verify and consume a backup code
        Each backup code can only be used once
        """
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        backup_code = self.db.query(MFABackupCode).filter(
            MFABackupCode.user_id == user.id,
            MFABackupCode.code_hash == code_hash,
            MFABackupCode.used_at == None
        ).first()
        
        if not backup_code:
            logger.warning(f"Invalid backup code attempt for user {user.email}")
            return False
        
        # Mark as used
        backup_code.used_at = datetime.now(timezone.utc)
        self.db.commit()
        
        logger.info(f"Backup code used for user {user.email}")
        return True
    
    def get_active_devices(self, user: User) -> list[MFADevice]:
        """Get all active MFA devices for user"""
        return self.db.query(MFADevice).filter(
            MFADevice.user_id == user.id,
            MFADevice.is_active == True
        ).all()
    
    def disable_device(self, device_id: int, user: User) -> bool:
        """Disable an MFA device"""
        device = self.db.query(MFADevice).filter(
            MFADevice.id == device_id,
            MFADevice.user_id == user.id
        ).first()
        
        if not device:
            return False
        
        device.is_active = False
        device.disabled_at = datetime.now(timezone.utc)
        self.db.commit()
        
        logger.info(f"MFA device disabled: {device_id}")
        return True
    
    def is_mfa_required(self, user: User) -> bool:
        """
        Check if MFA is required for user
        FedRAMP High requires MFA for all privileged users
        """
        # Check organization MFA policy
        if hasattr(user, 'org') and user.org:
            if getattr(user.org, 'require_mfa', False):
                return True
        
        # Always require for admin/founder roles (privileged users)
        privileged_roles = ['admin', 'founder']
        if user.role in privileged_roles:
            return True
        
        # Check settings
        if settings.ENV == "production":
            # FedRAMP requires MFA for all users in production
            return True
        
        return False
    
    def is_mfa_enrolled(self, user: User) -> bool:
        """Check if user has at least one active MFA device"""
        active_devices = self.get_active_devices(user)
        return len(active_devices) > 0
    
    def _encrypt_secret(self, secret: str) -> str:
        """
        Encrypt TOTP secret for storage
        Should use FIPS 140-2 validated encryption in production
        """
        # TODO: Replace with FIPS 140-2 validated encryption
        # For now, using base64 encoding (NOT SECURE - placeholder only)
        # In production, use AWS KMS, Azure Key Vault, or HSM
        return base64.b64encode(secret.encode()).decode()
    
    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt stored TOTP secret
        Should use FIPS 140-2 validated decryption in production
        """
        # TODO: Replace with FIPS 140-2 validated decryption
        return base64.b64decode(encrypted_secret.encode()).decode()
