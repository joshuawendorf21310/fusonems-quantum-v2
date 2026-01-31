"""
Key Management Service for cryptographic key lifecycle management.

This service handles:
- Key generation (FIPS-compliant)
- Key rotation (automated)
- Key lifecycle management
- Key escrow for recovery
- HSM integration placeholder

FedRAMP SC-12: Cryptographic key establishment and management.
FedRAMP SC-13: Use FIPS 140-2 validated cryptographic modules.
"""

import os
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, asdict

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.orm import Session

from core.database import Base
from core.crypto import (
    generate_key,
    encrypt_aes256_gcm_base64,
    decrypt_aes256_gcm_base64,
    get_random_bytes,
    hash_sha256,
    is_fips_enabled
)
from core.config import settings

logger = logging.getLogger(__name__)


class KeyStatus(Enum):
    """Key lifecycle status."""
    ACTIVE = "active"
    ROTATING = "rotating"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class KeyType(Enum):
    """Key type classification."""
    ENCRYPTION = "encryption"
    SIGNING = "signing"
    MAC = "mac"
    DERIVATION = "derivation"


@dataclass
class KeyMetadata:
    """Key metadata for lifecycle management."""
    key_id: str
    key_type: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    rotated_at: Optional[datetime]
    rotation_interval_days: int
    usage_count: int
    last_used_at: Optional[datetime]
    hsm_backed: bool
    escrowed: bool


class EncryptionKey(Base):
    """Database model for encryption key storage."""
    __tablename__ = "encryption_keys"
    
    id = Column(Integer, primary_key=True)
    key_id = Column(String(64), unique=True, nullable=False, index=True)
    key_type = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="active")
    
    # Encrypted key material (encrypted with master key)
    encrypted_key = Column(Text, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    rotated_at = Column(DateTime, nullable=True)
    rotation_interval_days = Column(Integer, nullable=False, default=90)
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # HSM and escrow flags
    hsm_backed = Column(Boolean, nullable=False, default=False)
    escrowed = Column(Boolean, nullable=False, default=False)
    escrow_location = Column(String(256), nullable=True)
    
    # Key metadata (JSON)
    metadata_json = Column(Text, nullable=True)


class KeyManagementService:
    """
    Service for managing cryptographic keys with FIPS compliance.
    
    Features:
    - FIPS-compliant key generation
    - Automated key rotation
    - Key escrow for recovery
    - HSM integration placeholder
    """
    
    def __init__(self, db: Session, master_key: Optional[bytes] = None):
        """
        Initialize key management service.
        
        Args:
            db: Database session
            master_key: Master key for encrypting stored keys (defaults to settings)
        """
        self.db = db
        self._master_key = master_key or self._get_master_key()
        self._key_cache: Dict[str, bytes] = {}
        self._cache_ttl = timedelta(hours=1)
    
    def _get_master_key(self) -> bytes:
        """
        Get master key for encrypting stored keys.
        
        Uses KEY_MANAGEMENT_MASTER_KEY from settings, or generates a warning.
        """
        master_key_str = getattr(settings, "KEY_MANAGEMENT_MASTER_KEY", None)
        if not master_key_str:
            logger.warning(
                "KEY_MANAGEMENT_MASTER_KEY not set. Using default (NOT SECURE FOR PRODUCTION)."
            )
            # Generate a deterministic key from settings (NOT SECURE, but allows testing)
            # In production, this MUST be set explicitly
            fallback = getattr(settings, "STORAGE_ENCRYPTION_KEY", "default-master-key-not-set")
            return hash_sha256(fallback.encode("utf-8"))
        
        # Master key should be 32 bytes (256 bits) for AES-256
        if len(master_key_str) >= 32:
            return hash_sha256(master_key_str.encode("utf-8"))[:32]
        else:
            # Pad or hash to get 32 bytes
            return hash_sha256(master_key_str.encode("utf-8"))[:32]
    
    def generate_key(
        self,
        key_type: KeyType = KeyType.ENCRYPTION,
        key_length: int = 32,
        rotation_interval_days: int = 90,
        hsm_backed: bool = False,
        escrow: bool = False
    ) -> str:
        """
        Generate a new cryptographic key.
        
        Args:
            key_type: Type of key to generate
            key_length: Key length in bytes (default 32 for AES-256)
            rotation_interval_days: Days until key should be rotated
            hsm_backed: Whether key is backed by HSM (placeholder)
            escrow: Whether to escrow the key
        
        Returns:
            Key ID for the generated key
        """
        # Generate key material
        if hsm_backed:
            # Placeholder: In production, this would interface with HSM
            logger.info("HSM-backed key generation requested (placeholder)")
            key_material = self._generate_hsm_key(key_length)
        else:
            key_material = generate_key(key_length)
        
        # Generate unique key ID
        key_id = self._generate_key_id(key_type, key_material)
        
        # Encrypt key material with master key
        encrypted_key = encrypt_aes256_gcm_base64(
            base64.b64encode(key_material).decode("utf-8"),
            self._master_key,
            associated_data=key_id
        )
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=rotation_interval_days)
        
        # Store in database
        db_key = EncryptionKey(
            key_id=key_id,
            key_type=key_type.value,
            status=KeyStatus.ACTIVE.value,
            encrypted_key=encrypted_key,
            expires_at=expires_at,
            rotation_interval_days=rotation_interval_days,
            hsm_backed=hsm_backed,
            escrowed=escrow,
            metadata_json=json.dumps({
                "key_length": key_length,
                "fips_enabled": is_fips_enabled(),
                "created_by": "key_management_service"
            })
        )
        
        self.db.add(db_key)
        self.db.commit()
        
        # Escrow key if requested
        if escrow:
            self._escrow_key(key_id, key_material)
        
        logger.info(f"Generated new {key_type.value} key: {key_id}")
        return key_id
    
    def _generate_hsm_key(self, key_length: int) -> bytes:
        """
        Placeholder for HSM key generation.
        
        In production, this would interface with an HSM (Hardware Security Module)
        to generate keys that never leave the HSM.
        
        Args:
            key_length: Desired key length
            
        Returns:
            Key material (in production, this would be a handle/reference)
        """
        # For now, generate normally but mark as HSM-backed
        # In production, replace with actual HSM API calls
        logger.warning("HSM integration not implemented, using software key generation")
        return generate_key(key_length)
    
    def _generate_key_id(self, key_type: KeyType, key_material: bytes) -> str:
        """
        Generate a unique key ID.
        
        Args:
            key_type: Type of key
            key_material: Key material
            
        Returns:
            Unique key ID
        """
        # Use hash of key material + timestamp for uniqueness
        timestamp = datetime.utcnow().isoformat()
        combined = f"{key_type.value}:{base64.b64encode(key_material).decode()}:{timestamp}"
        key_hash = hash_sha256(combined.encode("utf-8"))
        return f"{key_type.value}_{base64.urlsafe_b64encode(key_hash[:16]).decode().rstrip('=')}"
    
    def get_key(self, key_id: str, use_cache: bool = True) -> Optional[bytes]:
        """
        Retrieve a key by ID.
        
        Args:
            key_id: Key ID
            use_cache: Whether to use cached key
            
        Returns:
            Decrypted key material, or None if not found
        """
        # Check cache first
        if use_cache and key_id in self._key_cache:
            return self._key_cache[key_id]
        
        # Query database
        db_key = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_id == key_id
        ).first()
        
        if not db_key:
            return None
        
        # Check status
        if db_key.status == KeyStatus.REVOKED.value:
            logger.warning(f"Attempted to use revoked key: {key_id}")
            return None
        
        # Decrypt key material
        try:
            encrypted_key_str = db_key.encrypted_key
            decrypted_key_str = decrypt_aes256_gcm_base64(
                encrypted_key_str,
                self._master_key,
                associated_data=key_id
            )
            key_material = base64.b64decode(decrypted_key_str)
            
            # Update usage tracking
            db_key.usage_count += 1
            db_key.last_used_at = datetime.utcnow()
            self.db.commit()
            
            # Cache key
            if use_cache:
                self._key_cache[key_id] = key_material
            
            return key_material
        
        except Exception as e:
            logger.error(f"Failed to decrypt key {key_id}: {e}")
            return None
    
    def rotate_key(self, key_id: str, force: bool = False) -> Optional[str]:
        """
        Rotate a key by generating a new version.
        
        Args:
            key_id: Key ID to rotate
            force: Force rotation even if not expired
            
        Returns:
            New key ID, or None if rotation failed
        """
        db_key = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_id == key_id
        ).first()
        
        if not db_key:
            logger.error(f"Key not found for rotation: {key_id}")
            return None
        
        # Check if rotation is needed
        if not force:
            if db_key.status == KeyStatus.REVOKED.value:
                logger.warning(f"Cannot rotate revoked key: {key_id}")
                return None
            
            if db_key.expires_at and db_key.expires_at > datetime.utcnow():
                logger.info(f"Key {key_id} not yet expired, skipping rotation")
                return None
        
        # Mark old key as deprecated
        db_key.status = KeyStatus.DEPRECATED.value
        db_key.rotated_at = datetime.utcnow()
        
        # Generate new key
        new_key_id = self.generate_key(
            key_type=KeyType(db_key.key_type),
            rotation_interval_days=db_key.rotation_interval_days,
            hsm_backed=db_key.hsm_backed,
            escrow=db_key.escrowed
        )
        
        self.db.commit()
        
        logger.info(f"Rotated key {key_id} -> {new_key_id}")
        return new_key_id
    
    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke a key (mark as revoked, do not delete for audit).
        
        Args:
            key_id: Key ID to revoke
            
        Returns:
            True if revoked successfully
        """
        db_key = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_id == key_id
        ).first()
        
        if not db_key:
            return False
        
        db_key.status = KeyStatus.REVOKED.value
        self.db.commit()
        
        # Remove from cache
        self._key_cache.pop(key_id, None)
        
        logger.warning(f"Revoked key: {key_id}")
        return True
    
    def list_keys(
        self,
        key_type: Optional[KeyType] = None,
        status: Optional[KeyStatus] = None
    ) -> List[KeyMetadata]:
        """
        List keys matching criteria.
        
        Args:
            key_type: Filter by key type
            status: Filter by status
            
        Returns:
            List of key metadata
        """
        query = self.db.query(EncryptionKey)
        
        if key_type:
            query = query.filter(EncryptionKey.key_type == key_type.value)
        
        if status:
            query = query.filter(EncryptionKey.status == status.value)
        
        keys = query.all()
        
        return [
            KeyMetadata(
                key_id=key.key_id,
                key_type=key.key_type,
                status=key.status,
                created_at=key.created_at,
                expires_at=key.expires_at,
                rotated_at=key.rotated_at,
                rotation_interval_days=key.rotation_interval_days,
                usage_count=key.usage_count,
                last_used_at=key.last_used_at,
                hsm_backed=key.hsm_backed,
                escrowed=key.escrowed
            )
            for key in keys
        ]
    
    def check_rotation_needed(self) -> List[str]:
        """
        Check which keys need rotation.
        
        Returns:
            List of key IDs that need rotation
        """
        now = datetime.utcnow()
        keys_to_rotate = self.db.query(EncryptionKey).filter(
            EncryptionKey.status == KeyStatus.ACTIVE.value,
            EncryptionKey.expires_at <= now
        ).all()
        
        return [key.key_id for key in keys_to_rotate]
    
    def auto_rotate_expired_keys(self) -> List[str]:
        """
        Automatically rotate all expired keys.
        
        Returns:
            List of new key IDs created
        """
        expired_key_ids = self.check_rotation_needed()
        rotated_keys = []
        
        for key_id in expired_key_ids:
            new_key_id = self.rotate_key(key_id, force=True)
            if new_key_id:
                rotated_keys.append(new_key_id)
        
        if rotated_keys:
            logger.info(f"Auto-rotated {len(rotated_keys)} expired keys")
        
        return rotated_keys
    
    def _escrow_key(self, key_id: str, key_material: bytes) -> bool:
        """
        Escrow key for recovery purposes.
        
        This is a placeholder implementation. In production, keys should be
        escrowed to a secure, separate system with proper access controls.
        
        Args:
            key_id: Key ID
            key_material: Key material to escrow
            
        Returns:
            True if escrowed successfully
        """
        # Placeholder: In production, this would:
        # 1. Encrypt key with escrow master key
        # 2. Store in separate secure system
        # 3. Implement proper access controls and audit logging
        
        escrow_location = getattr(settings, "KEY_ESCROW_LOCATION", None)
        if not escrow_location:
            logger.warning(f"KEY_ESCROW_LOCATION not set, key {key_id} not escrowed")
            return False
        
        # Update database record
        db_key = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_id == key_id
        ).first()
        
        if db_key:
            db_key.escrowed = True
            db_key.escrow_location = escrow_location
            self.db.commit()
        
        logger.info(f"Escrowed key {key_id} to {escrow_location}")
        return True
    
    def recover_key_from_escrow(self, key_id: str) -> Optional[bytes]:
        """
        Recover a key from escrow.
        
        This is a placeholder implementation. In production, this would
        require proper authorization and audit logging.
        
        Args:
            key_id: Key ID to recover
            
        Returns:
            Recovered key material, or None if recovery failed
        """
        # Placeholder: In production, this would:
        # 1. Verify authorization
        # 2. Retrieve from escrow system
        # 3. Decrypt with escrow master key
        # 4. Log recovery event
        
        logger.warning(f"Key recovery from escrow requested for {key_id} (placeholder)")
        return None
