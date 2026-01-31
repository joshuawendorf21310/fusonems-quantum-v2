"""
PS-6: Access Agreements Service
Implements FedRAMP PS-6 requirements for NDA/confidentiality agreement tracking, signature management, and annual renewal.
"""
import logging
import hashlib
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.personnel_security import AccessAgreement, AgreementStatus
from models.user import User
from core.logger import logger


class AccessAgreementsService:
    """Service for managing access agreements per FedRAMP PS-6"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_access_agreement(
        self,
        org_id: int,
        user_id: int,
        agreement_type: str,  # NDA, confidentiality, acceptable_use, etc.
        agreement_title: str,
        agreement_version: str,
        agreement_content: Optional[str] = None,
        agreement_document_path: Optional[str] = None,
        effective_date: Optional[date] = None,
        requires_renewal: bool = True,
        renewal_frequency_months: int = 12,
        created_by_user_id: int = None,
    ) -> AccessAgreement:
        """
        Create a new access agreement.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            agreement_type: Type of agreement
            agreement_title: Agreement title
            agreement_version: Agreement version
            agreement_content: Agreement content text (optional)
            agreement_document_path: Path to agreement document (optional)
            effective_date: Effective date (defaults to today)
            requires_renewal: Whether agreement requires renewal
            renewal_frequency_months: Renewal frequency in months
            created_by_user_id: User creating the agreement
            
        Returns:
            Created AccessAgreement
        """
        try:
            effective_date = effective_date or date.today()
            expiration_date = None
            next_renewal_date = None
            
            if requires_renewal:
                expiration_date = effective_date + timedelta(days=renewal_frequency_months * 30)
                next_renewal_date = expiration_date
            
            # Calculate content hash for integrity verification
            content_hash = None
            if agreement_content:
                content_hash = hashlib.sha256(agreement_content.encode()).hexdigest()
            
            agreement = AccessAgreement(
                org_id=org_id,
                user_id=user_id,
                agreement_type=agreement_type,
                agreement_title=agreement_title,
                agreement_version=agreement_version,
                status=AgreementStatus.PENDING,
                effective_date=effective_date,
                expiration_date=expiration_date,
                requires_renewal=requires_renewal,
                renewal_frequency_months=renewal_frequency_months,
                next_renewal_date=next_renewal_date,
                agreement_document_path=agreement_document_path,
                agreement_content_hash=content_hash,
                created_by_user_id=created_by_user_id,
            )
            
            self.db.add(agreement)
            self.db.commit()
            self.db.refresh(agreement)
            
            logger.info(
                f"Created access agreement for user {user_id}",
                extra={
                    "org_id": org_id,
                    "user_id": user_id,
                    "agreement_type": agreement_type,
                    "event_type": "access_agreement.created",
                }
            )
            
            return agreement
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create access agreement: {e}", exc_info=True)
            raise
    
    def sign_agreement(
        self,
        agreement_id: int,
        org_id: int,
        signature_method: str = "electronic",  # electronic, physical, digital
        signed_document_path: Optional[str] = None,
        signed_by_user_id: Optional[int] = None,
    ) -> AccessAgreement:
        """
        Sign an access agreement.
        
        Args:
            agreement_id: Agreement ID
            org_id: Organization ID (for verification)
            signature_method: Method of signature
            signed_document_path: Path to signed document
            signed_by_user_id: User signing (defaults to agreement user_id)
            
        Returns:
            Updated AccessAgreement
        """
        try:
            agreement = self.db.query(AccessAgreement).filter(
                AccessAgreement.id == agreement_id,
                AccessAgreement.org_id == org_id,
            ).first()
            
            if not agreement:
                raise ValueError(f"Access agreement {agreement_id} not found")
            
            signed_by_user_id = signed_by_user_id or agreement.user_id
            
            agreement.status = AgreementStatus.SIGNED
            agreement.signed_at = datetime.utcnow()
            agreement.signed_by_user_id = signed_by_user_id
            agreement.signature_method = signature_method
            agreement.signed_document_path = signed_document_path
            agreement.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(agreement)
            
            logger.info(
                f"Signed access agreement {agreement_id}",
                extra={
                    "org_id": org_id,
                    "agreement_id": agreement_id,
                    "user_id": agreement.user_id,
                    "event_type": "access_agreement.signed",
                }
            )
            
            return agreement
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to sign agreement: {e}", exc_info=True)
            raise
    
    def renew_agreement(
        self,
        agreement_id: int,
        org_id: int,
        new_effective_date: Optional[date] = None,
        new_agreement_version: Optional[str] = None,
    ) -> AccessAgreement:
        """
        Renew an access agreement.
        
        Args:
            agreement_id: Agreement ID
            org_id: Organization ID (for verification)
            new_effective_date: New effective date (defaults to today)
            new_agreement_version: New agreement version (optional)
            
        Returns:
            Updated AccessAgreement
        """
        try:
            agreement = self.db.query(AccessAgreement).filter(
                AccessAgreement.id == agreement_id,
                AccessAgreement.org_id == org_id,
            ).first()
            
            if not agreement:
                raise ValueError(f"Access agreement {agreement_id} not found")
            
            new_effective_date = new_effective_date or date.today()
            expiration_date = None
            next_renewal_date = None
            
            if agreement.requires_renewal:
                expiration_date = new_effective_date + timedelta(
                    days=agreement.renewal_frequency_months * 30
                )
                next_renewal_date = expiration_date
            
            agreement.status = AgreementStatus.RENEWED
            agreement.effective_date = new_effective_date
            agreement.expiration_date = expiration_date
            agreement.next_renewal_date = next_renewal_date
            
            if new_agreement_version:
                agreement.agreement_version = new_agreement_version
            
            # Reset signature status - needs to be signed again
            agreement.signed_at = None
            agreement.signed_by_user_id = None
            agreement.signed_document_path = None
            agreement.status = AgreementStatus.PENDING
            
            agreement.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(agreement)
            
            logger.info(
                f"Renewed access agreement {agreement_id}",
                extra={
                    "org_id": org_id,
                    "agreement_id": agreement_id,
                    "user_id": agreement.user_id,
                    "event_type": "access_agreement.renewed",
                }
            )
            
            return agreement
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to renew agreement: {e}", exc_info=True)
            raise
    
    def get_agreement(
        self,
        agreement_id: int,
        org_id: int,
    ) -> Optional[AccessAgreement]:
        """Get an access agreement by ID"""
        return self.db.query(AccessAgreement).filter(
            AccessAgreement.id == agreement_id,
            AccessAgreement.org_id == org_id,
        ).first()
    
    def list_agreements(
        self,
        org_id: int,
        user_id: Optional[int] = None,
        agreement_type: Optional[str] = None,
        status: Optional[AgreementStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AccessAgreement]:
        """
        List access agreements for an organization.
        
        Args:
            org_id: Organization ID
            user_id: Filter by user ID (optional)
            agreement_type: Filter by type (optional)
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of AccessAgreement
        """
        query = self.db.query(AccessAgreement).filter(
            AccessAgreement.org_id == org_id,
        )
        
        if user_id:
            query = query.filter(AccessAgreement.user_id == user_id)
        
        if agreement_type:
            query = query.filter(AccessAgreement.agreement_type == agreement_type)
        
        if status:
            query = query.filter(AccessAgreement.status == status)
        
        return query.order_by(
            AccessAgreement.effective_date.desc()
        ).limit(limit).offset(offset).all()
    
    def get_agreements_due_for_renewal(
        self,
        org_id: int,
        days_ahead: int = 30,
    ) -> List[AccessAgreement]:
        """
        Get access agreements due for renewal.
        
        Args:
            org_id: Organization ID
            days_ahead: Number of days ahead to check (default 30)
            
        Returns:
            List of AccessAgreement due for renewal
        """
        today = date.today()
        threshold = today + timedelta(days=days_ahead)
        
        return self.db.query(AccessAgreement).filter(
            AccessAgreement.org_id == org_id,
            AccessAgreement.requires_renewal == True,
            AccessAgreement.next_renewal_date <= threshold,
            AccessAgreement.status == AgreementStatus.SIGNED,
        ).order_by(AccessAgreement.next_renewal_date).all()
    
    def get_expired_agreements(
        self,
        org_id: int,
    ) -> List[AccessAgreement]:
        """
        Get expired access agreements.
        
        Args:
            org_id: Organization ID
            
        Returns:
            List of expired AccessAgreement
        """
        today = date.today()
        
        agreements = self.db.query(AccessAgreement).filter(
            AccessAgreement.org_id == org_id,
            AccessAgreement.expiration_date <= today,
            AccessAgreement.status == AgreementStatus.SIGNED,
        ).all()
        
        # Update status to expired
        for agreement in agreements:
            agreement.status = AgreementStatus.EXPIRED
            agreement.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return agreements
