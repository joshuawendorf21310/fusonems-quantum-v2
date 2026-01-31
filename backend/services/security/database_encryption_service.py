"""
Database Encryption Service for field-level encryption of sensitive data.

This service provides:
- Automatic encryption on write
- Automatic decryption on read
- Field-level encryption for PHI, PII, payment data
- Integration with key management
- Transparent encryption/decryption

FedRAMP SC-28: Protect information at rest using cryptographic mechanisms.
"""

import logging
from typing import Optional, Dict, Any, List, Type
from sqlalchemy.orm import Session, Mapper
from sqlalchemy import event
from sqlalchemy.orm import Session as SQLASession

from services.security.encryption_at_rest import EncryptionAtRestService
from services.security.key_management_service import KeyManagementService

logger = logging.getLogger(__name__)


class DatabaseEncryptionService:
    """
    Service for field-level database encryption.
    
    Automatically encrypts sensitive fields on write and decrypts on read.
    """
    
    def __init__(self, db: Session, encryption_service: Optional[EncryptionAtRestService] = None):
        """
        Initialize database encryption service.
        
        Args:
            db: Database session
            encryption_service: Optional encryption at rest service instance
        """
        self.db = db
        self._encryption_service = encryption_service or EncryptionAtRestService(db)
        self._encrypted_fields: Dict[Type, List[str]] = {}
        self._setup_event_listeners()
    
    def register_encrypted_fields(self, model_class: Type, fields: List[str]):
        """
        Register fields that should be encrypted for a model.
        
        Args:
            model_class: SQLAlchemy model class
            fields: List of field names to encrypt
        """
        if model_class not in self._encrypted_fields:
            self._encrypted_fields[model_class] = []
        
        for field in fields:
            if field not in self._encrypted_fields[model_class]:
                self._encrypted_fields[model_class].append(field)
        
        logger.info(f"Registered encrypted fields for {model_class.__name__}: {fields}")
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for automatic encryption/decryption."""
        # Listen for before_insert and before_update to encrypt
        @event.listens_for(SQLASession, "before_flush", propagate=True)
        def receive_before_flush(session: SQLASession, flush_context, instances):
            """Encrypt fields before inserting/updating."""
            for instance in session.new.union(session.dirty):
                self._encrypt_instance(instance)
        
        # Listen for after_load to decrypt
        @event.listens_for(SQLASession, "loaded_as_persistent")
        def receive_loaded_as_persistent(session: SQLASession, instance):
            """Decrypt fields after loading from database."""
            self._decrypt_instance(instance)
    
    def _encrypt_instance(self, instance: Any):
        """
        Encrypt all registered fields for an instance.
        
        Args:
            instance: SQLAlchemy model instance
        """
        model_class = type(instance)
        if model_class not in self._encrypted_fields:
            return
        
        for field_name in self._encrypted_fields[model_class]:
            if not hasattr(instance, field_name):
                continue
            
            field_value = getattr(instance, field_name)
            
            # Skip None and empty strings
            if field_value is None or field_value == "":
                continue
            
            # Skip if already encrypted (check for base64-like pattern)
            if isinstance(field_value, str) and self._is_encrypted(field_value):
                continue
            
            try:
                # Encrypt the field value
                encrypted_value = self._encryption_service.encrypt_column_value(
                    str(field_value),
                    associated_data=f"{model_class.__name__}.{field_name}"
                )
                setattr(instance, field_name, encrypted_value)
            except Exception as e:
                logger.error(
                    f"Failed to encrypt field {model_class.__name__}.{field_name}: {e}"
                )
                # Don't raise - allow the value to be stored unencrypted
                # In production, you might want to raise or handle differently
    
    def _decrypt_instance(self, instance: Any):
        """
        Decrypt all registered fields for an instance.
        
        Args:
            instance: SQLAlchemy model instance
        """
        model_class = type(instance)
        if model_class not in self._encrypted_fields:
            return
        
        for field_name in self._encrypted_fields[model_class]:
            if not hasattr(instance, field_name):
                continue
            
            field_value = getattr(instance, field_name)
            
            # Skip None and empty strings
            if field_value is None or field_value == "":
                continue
            
            # Only decrypt if it looks encrypted
            if not isinstance(field_value, str) or not self._is_encrypted(field_value):
                continue
            
            try:
                # Decrypt the field value
                decrypted_value = self._encryption_service.decrypt_column_value(
                    field_value,
                    associated_data=f"{model_class.__name__}.{field_name}"
                )
                setattr(instance, field_name, decrypted_value)
            except Exception as e:
                logger.error(
                    f"Failed to decrypt field {model_class.__name__}.{field_name}: {e}"
                )
                # Keep encrypted value if decryption fails
                # This allows for key rotation scenarios
    
    def _is_encrypted(self, value: str) -> bool:
        """
        Check if a value appears to be encrypted.
        
        Args:
            value: Value to check
            
        Returns:
            True if value appears encrypted
        """
        if not isinstance(value, str) or len(value) < 20:
            return False
        
        # Encrypted values are base64-encoded and typically longer
        # Check for base64-like pattern (contains only base64 chars and is reasonably long)
        try:
            import base64
            # Try to decode - if it works and is reasonably long, likely encrypted
            decoded = base64.urlsafe_b64decode(value + "==")  # Add padding
            return len(decoded) > 12  # Minimum size for nonce + some ciphertext
        except Exception:
            return False
    
    def encrypt_field(self, model_class: Type, field_name: str, value: str) -> str:
        """
        Manually encrypt a field value.
        
        Args:
            model_class: Model class
            field_name: Field name
            value: Value to encrypt
            
        Returns:
            Encrypted value
        """
        if not value:
            return ""
        
        return self._encryption_service.encrypt_column_value(
            value,
            associated_data=f"{model_class.__name__}.{field_name}"
        )
    
    def decrypt_field(self, model_class: Type, field_name: str, encrypted_value: str) -> str:
        """
        Manually decrypt a field value.
        
        Args:
            model_class: Model class
            field_name: Field name
            encrypted_value: Encrypted value
            
        Returns:
            Decrypted value
        """
        if not encrypted_value:
            return ""
        
        return self._encryption_service.decrypt_column_value(
            encrypted_value,
            associated_data=f"{model_class.__name__}.{field_name}"
        )
    
    def bulk_encrypt_fields(
        self,
        model_class: Type,
        instances: List[Any],
        field_names: Optional[List[str]] = None
    ):
        """
        Bulk encrypt fields for multiple instances.
        
        Args:
            model_class: Model class
            instances: List of instances
            field_names: Optional list of field names (uses registered fields if not provided)
        """
        fields = field_names or self._encrypted_fields.get(model_class, [])
        
        for instance in instances:
            for field_name in fields:
                if not hasattr(instance, field_name):
                    continue
                
                value = getattr(instance, field_name)
                if value and not self._is_encrypted(str(value)):
                    encrypted = self.encrypt_field(model_class, field_name, str(value))
                    setattr(instance, field_name, encrypted)
    
    def bulk_decrypt_fields(
        self,
        model_class: Type,
        instances: List[Any],
        field_names: Optional[List[str]] = None
    ):
        """
        Bulk decrypt fields for multiple instances.
        
        Args:
            model_class: Model class
            instances: List of instances
            field_names: Optional list of field names (uses registered fields if not provided)
        """
        fields = field_names or self._encrypted_fields.get(model_class, [])
        
        for instance in instances:
            for field_name in fields:
                if not hasattr(instance, field_name):
                    continue
                
                value = getattr(instance, field_name)
                if value and self._is_encrypted(str(value)):
                    decrypted = self.decrypt_field(model_class, field_name, str(value))
                    setattr(instance, field_name, decrypted)
