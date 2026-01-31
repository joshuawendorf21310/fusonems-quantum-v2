"""
Initialize encryption at rest for models.

This module registers encrypted fields for models to enable automatic
encryption/decryption via DatabaseEncryptionService.

FedRAMP SC-28: Protect information at rest using cryptographic mechanisms.
"""

import logging
from sqlalchemy.orm import Session

from services.security.database_encryption_service import DatabaseEncryptionService
from models.epcr_core import Patient, MasterPatient
from models.telehealth import TelehealthPatient
from models.user import User
from models.patient_portal import PatientPayment, StripeCustomer
from models.billing import BillingRecord

logger = logging.getLogger(__name__)


def initialize_encryption(db: Session) -> DatabaseEncryptionService:
    """
    Initialize encryption service and register encrypted fields for all models.
    
    Args:
        db: Database session
        
    Returns:
        Initialized DatabaseEncryptionService instance
    """
    encryption_service = DatabaseEncryptionService(db)
    
    # Register PHI fields in Patient model (epcr_core)
    encryption_service.register_encrypted_fields(
        Patient,
        [
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "phone",
            "address",
            "mrn",
        ]
    )
    
    # Register PHI fields in MasterPatient
    encryption_service.register_encrypted_fields(
        MasterPatient,
        [
            "first_name",
            "last_name",
            "date_of_birth",
            "phone",
            "address",
        ]
    )
    
    # Register PHI fields in TelehealthPatient
    encryption_service.register_encrypted_fields(
        TelehealthPatient,
        [
            "name",
            "email",
            "phone",
            "address",
            "insurance_policy_number",
            "medical_history",
            "allergies",
            "current_medications",
        ]
    )
    
    # Register PII fields in User model
    encryption_service.register_encrypted_fields(
        User,
        [
            "email",
            "full_name",
        ]
    )
    
    # Register payment fields
    encryption_service.register_encrypted_fields(
        PatientPayment,
        [
            "payment_method_last4",
        ]
    )
    
    encryption_service.register_encrypted_fields(
        StripeCustomer,
        [
            "email",
            "name",
            "default_payment_method",
        ]
    )
    
    # Register billing sensitive fields
    encryption_service.register_encrypted_fields(
        BillingRecord,
        [
            "patient_name",
        ]
    )
    
    logger.info("Encryption at rest initialized for all registered models")
    return encryption_service
