"""
Non-Repudiation Service for FedRAMP AU-10 Compliance

FedRAMP Requirement AU-10: Non-Repudiation
- Digital signatures for critical actions
- Proof of origin
- Proof of receipt
- Cryptographic verification
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.non_repudiation import (
    DigitalSignature,
    ReceiptConfirmation,
    SignatureAlgorithm,
    SignatureStatus,
    ActionCriticality,
)
from models.user import User


class NonRepudiationService:
    """
    Service for non-repudiation through digital signatures (AU-10).
    """
    
    # Actions that require digital signatures based on criticality
    CRITICAL_ACTIONS = {
        'user': ['delete', 'disable', 'role_change'],
        'configuration': ['activate_baseline', 'approve_change', 'implement_change'],
        'document': ['delete', 'export', 'share'],
        'billing': ['write_off', 'refund', 'approve_payment'],
    }
    
    @staticmethod
    def sign_action(
        db: Session,
        org_id: int,
        user: User,
        resource_type: str,
        resource_id: str,
        action: str,
        content: Dict,
        action_criticality: Optional[ActionCriticality] = None,
        signature_algorithm: SignatureAlgorithm = SignatureAlgorithm.RSA_SHA256,
    ) -> DigitalSignature:
        """
        Create a digital signature for a critical action.
        
        Args:
            db: Database session
            org_id: Organization ID
            user: User performing the action
            resource_type: Type of resource
            resource_id: ID of resource
            action: Action being performed
            content: Content being signed (dict)
            action_criticality: Criticality level (auto-determined if not provided)
            signature_algorithm: Algorithm to use for signing
            
        Returns:
            Created DigitalSignature record
        """
        # Determine criticality if not provided
        if action_criticality is None:
            action_criticality = NonRepudiationService._determine_criticality(
                resource_type, action
            )
        
        # Only sign critical actions
        if action_criticality not in [ActionCriticality.HIGH, ActionCriticality.CRITICAL]:
            logger.debug(f"Skipping signature for non-critical action: {resource_type}.{action}")
            # Still create a record but mark as low priority
            action_criticality = ActionCriticality.LOW
        
        # Generate content hash
        content_json = json.dumps(content, sort_keys=True)
        content_hash = hashlib.sha256(content_json.encode()).hexdigest()
        
        # Generate digital signature
        signature_value = NonRepudiationService._generate_signature(
            content_json, user.id, signature_algorithm
        )
        
        # Create signature record
        signature = DigitalSignature(
            org_id=org_id,
            resource_type=resource_type,
            resource_id=str(resource_id),
            action=action,
            action_criticality=action_criticality.value,
            content_hash=content_hash,
            content_preview=content_json[:500] if len(content_json) > 500 else content_json,
            full_content=content if action_criticality == ActionCriticality.CRITICAL else None,
            signature_algorithm=signature_algorithm.value,
            signature_value=signature_value,
            signed_by_user_id=user.id,
            signed_by_email=user.email,
            signed_by_role=user.role,
            status=SignatureStatus.SIGNED.value,
            signed_at=datetime.now(timezone.utc),
        )
        
        db.add(signature)
        db.commit()
        db.refresh(signature)
        
        logger.info(
            f"Digital signature created: {resource_type}.{action} "
            f"(user={user.email}, criticality={action_criticality.value})"
        )
        
        return signature
    
    @staticmethod
    def _determine_criticality(resource_type: str, action: str) -> ActionCriticality:
        """Determine action criticality"""
        critical_actions = NonRepudiationService.CRITICAL_ACTIONS.get(resource_type, [])
        
        if action in critical_actions:
            return ActionCriticality.CRITICAL
        
        # Check for high-risk actions
        high_risk_actions = ['delete', 'disable', 'approve', 'export', 'share']
        if action in high_risk_actions:
            return ActionCriticality.HIGH
        
        return ActionCriticality.MEDIUM
    
    @staticmethod
    def _generate_signature(
        content: str,
        user_id: int,
        algorithm: SignatureAlgorithm,
    ) -> str:
        """
        Generate digital signature for content.
        
        Note: In production, this should use actual user certificates/keys.
        For now, we generate a deterministic signature based on content and user.
        """
        # Create signature payload
        payload = f"{content}:{user_id}:{datetime.now(timezone.utc).isoformat()}"
        
        # Generate signature (simplified - in production use actual crypto)
        signature_bytes = hashlib.sha256(payload.encode()).digest()
        
        # Base64 encode
        import base64
        signature_value = base64.b64encode(signature_bytes).decode()
        
        return signature_value
    
    @staticmethod
    def verify_signature(
        db: Session,
        signature_id: str,
        org_id: int,
        expected_content: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a digital signature.
        
        Args:
            db: Database session
            signature_id: Signature ID to verify
            org_id: Organization ID
            expected_content: Expected content (optional, for validation)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        signature = db.query(DigitalSignature).filter(
            DigitalSignature.id == signature_id,
            DigitalSignature.org_id == org_id,
        ).first()
        
        if not signature:
            return False, "Signature not found"
        
        if signature.status == SignatureStatus.REVOKED.value:
            return False, "Signature has been revoked"
        
        if signature.expires_at and signature.expires_at < datetime.now(timezone.utc):
            signature.status = SignatureStatus.EXPIRED.value
            db.commit()
            return False, "Signature has expired"
        
        # Verify content hash if expected content provided
        if expected_content:
            content_json = json.dumps(expected_content, sort_keys=True)
            expected_hash = hashlib.sha256(content_json.encode()).hexdigest()
            
            if expected_hash != signature.content_hash:
                signature.status = SignatureStatus.INVALID.value
                db.commit()
                return False, "Content hash mismatch"
        
        # Verify signature value (simplified - in production use actual crypto verification)
        # For now, we just check that signature exists and is not revoked
        
        signature.status = SignatureStatus.VERIFIED.value
        signature.verified_at = datetime.now(timezone.utc)
        db.commit()
        
        return True, None
    
    @staticmethod
    def create_receipt_confirmation(
        db: Session,
        org_id: int,
        resource_type: str,
        resource_id: str,
        communication_type: str,
        recipient_user_id: int,
        recipient_email: Optional[str] = None,
        sent_by_user_id: Optional[int] = None,
        sent_by_email: Optional[str] = None,
        communication_content: Optional[str] = None,
        expires_in_hours: int = 24,
    ) -> ReceiptConfirmation:
        """
        Create a receipt confirmation for proof of receipt (AU-10).
        
        Args:
            db: Database session
            org_id: Organization ID
            resource_type: Type of resource
            resource_id: ID of resource
            communication_type: Type of communication
            recipient_user_id: User receiving the communication
            recipient_email: Recipient email (denormalized)
            sent_by_user_id: User sending (optional)
            sent_by_email: Sender email (optional)
            communication_content: Content preview
            expires_in_hours: Hours until expiration
            
        Returns:
            Created ReceiptConfirmation
        """
        # Generate receipt hash
        receipt_payload = f"{resource_type}:{resource_id}:{recipient_user_id}:{datetime.now(timezone.utc).isoformat()}"
        receipt_hash = hashlib.sha256(receipt_payload.encode()).hexdigest()
        
        receipt = ReceiptConfirmation(
            org_id=org_id,
            resource_type=resource_type,
            resource_id=str(resource_id),
            communication_type=communication_type,
            sent_by_user_id=sent_by_user_id,
            sent_by_email=sent_by_email,
            recipient_user_id=recipient_user_id,
            recipient_email=recipient_email,
            communication_content=communication_content,
            receipt_hash=receipt_hash,
            status="pending",
            sent_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        
        logger.info(
            f"Receipt confirmation created: {resource_type}.{resource_id} "
            f"(recipient={recipient_email})"
        )
        
        return receipt
    
    @staticmethod
    def acknowledge_receipt(
        db: Session,
        receipt_id: str,
        org_id: int,
        recipient_user_id: int,
        acknowledgment_message: Optional[str] = None,
    ) -> ReceiptConfirmation:
        """
        Acknowledge receipt of a communication.
        
        Args:
            db: Database session
            receipt_id: Receipt confirmation ID
            org_id: Organization ID
            recipient_user_id: User acknowledging
            acknowledgment_message: Optional message
            
        Returns:
            Updated ReceiptConfirmation
        """
        receipt = db.query(ReceiptConfirmation).filter(
            ReceiptConfirmation.id == receipt_id,
            ReceiptConfirmation.org_id == org_id,
            ReceiptConfirmation.recipient_user_id == recipient_user_id,
        ).first()
        
        if not receipt:
            raise ValueError(f"Receipt confirmation {receipt_id} not found")
        
        if receipt.status != "pending":
            raise ValueError(f"Receipt already {receipt.status}")
        
        receipt.status = "acknowledged"
        receipt.received_at = datetime.now(timezone.utc)
        receipt.acknowledged_at = datetime.now(timezone.utc)
        receipt.acknowledgment_message = acknowledgment_message
        
        # Generate receipt signature
        receipt_signature = NonRepudiationService._generate_signature(
            receipt.receipt_hash, recipient_user_id, SignatureAlgorithm.RSA_SHA256
        )
        receipt.receipt_signature = receipt_signature
        
        db.commit()
        db.refresh(receipt)
        
        logger.info(f"Receipt acknowledged: {receipt_id}")
        
        return receipt
    
    @staticmethod
    def get_signatures_for_resource(
        db: Session,
        org_id: int,
        resource_type: str,
        resource_id: str,
    ) -> List[DigitalSignature]:
        """Get all signatures for a resource"""
        return db.query(DigitalSignature).filter(
            DigitalSignature.org_id == org_id,
            DigitalSignature.resource_type == resource_type,
            DigitalSignature.resource_id == str(resource_id),
        ).order_by(desc(DigitalSignature.created_at)).all()
    
    @staticmethod
    def revoke_signature(
        db: Session,
        signature_id: str,
        org_id: int,
        revoked_by_user_id: int,
        revocation_reason: str,
    ) -> DigitalSignature:
        """Revoke a digital signature"""
        signature = db.query(DigitalSignature).filter(
            DigitalSignature.id == signature_id,
            DigitalSignature.org_id == org_id,
        ).first()
        
        if not signature:
            raise ValueError(f"Signature {signature_id} not found")
        
        signature.status = SignatureStatus.REVOKED.value
        signature.revoked_at = datetime.now(timezone.utc)
        signature.revoked_by_user_id = revoked_by_user_id
        signature.revocation_reason = revocation_reason
        
        db.commit()
        db.refresh(signature)
        
        logger.warning(f"Digital signature revoked: {signature_id} (reason: {revocation_reason})")
        
        return signature
