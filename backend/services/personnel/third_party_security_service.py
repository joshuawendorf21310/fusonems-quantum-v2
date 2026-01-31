"""
PS-7: Third-Party Personnel Security Service
Implements FedRAMP PS-7 requirements for third-party tracking, security requirements enforcement, and contract compliance.
"""
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.personnel_security import ThirdPartyPersonnel, ThirdPartyStatus
from models.user import User
from core.logger import logger


class ThirdPartySecurityService:
    """Service for managing third-party personnel security per FedRAMP PS-7"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_third_party_personnel(
        self,
        org_id: int,
        vendor_name: str,
        vendor_contact_name: str,
        vendor_contact_email: str,
        vendor_contact_phone: Optional[str] = None,
        personnel_name: str = None,
        personnel_email: str = None,
        personnel_phone: Optional[str] = None,
        personnel_role: str = None,
        contract_number: Optional[str] = None,
        contract_start_date: date = None,
        contract_end_date: Optional[date] = None,
        security_clearance_required: bool = False,
        security_clearance_level: Optional[str] = None,
        background_check_required: bool = True,
        nda_required: bool = True,
        notes: Optional[str] = None,
        created_by_user_id: int = None,
    ) -> ThirdPartyPersonnel:
        """
        Register third-party personnel.
        
        Args:
            org_id: Organization ID
            vendor_name: Vendor/contractor company name
            vendor_contact_name: Vendor contact person name
            vendor_contact_email: Vendor contact email
            vendor_contact_phone: Vendor contact phone (optional)
            personnel_name: Individual personnel name (if different from vendor contact)
            personnel_email: Individual personnel email
            personnel_phone: Individual personnel phone (optional)
            personnel_role: Role of the personnel
            contract_number: Contract number (optional)
            contract_start_date: Contract start date
            contract_end_date: Contract end date (optional)
            security_clearance_required: Whether security clearance is required
            security_clearance_level: Required clearance level
            background_check_required: Whether background check is required
            nda_required: Whether NDA is required
            notes: Additional notes
            created_by_user_id: User registering the personnel
            
        Returns:
            Created ThirdPartyPersonnel
        """
        try:
            # Use vendor contact info if personnel info not provided
            personnel_name = personnel_name or vendor_contact_name
            personnel_email = personnel_email or vendor_contact_email
            personnel_phone = personnel_phone or vendor_contact_phone
            
            contract_start_date = contract_start_date or date.today()
            
            third_party = ThirdPartyPersonnel(
                org_id=org_id,
                vendor_name=vendor_name,
                vendor_contact_name=vendor_contact_name,
                vendor_contact_email=vendor_contact_email,
                vendor_contact_phone=vendor_contact_phone,
                personnel_name=personnel_name,
                personnel_email=personnel_email,
                personnel_phone=personnel_phone,
                personnel_role=personnel_role or "Contractor",
                contract_number=contract_number,
                contract_start_date=contract_start_date,
                contract_end_date=contract_end_date,
                security_clearance_required=security_clearance_required,
                security_clearance_level=security_clearance_level,
                security_clearance_verified=False,
                background_check_required=background_check_required,
                background_check_completed=False,
                nda_required=nda_required,
                nda_signed=False,
                status=ThirdPartyStatus.ACTIVE,
                notes=notes,
                created_by_user_id=created_by_user_id,
            )
            
            self.db.add(third_party)
            self.db.commit()
            self.db.refresh(third_party)
            
            logger.info(
                f"Registered third-party personnel: {personnel_name} from {vendor_name}",
                extra={
                    "org_id": org_id,
                    "vendor_name": vendor_name,
                    "personnel_email": personnel_email,
                    "event_type": "third_party.registered",
                }
            )
            
            return third_party
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to register third-party personnel: {e}", exc_info=True)
            raise
    
    def verify_security_clearance(
        self,
        third_party_id: int,
        org_id: int,
        clearance_level: Optional[str] = None,
        verified_by_user_id: int = None,
    ) -> ThirdPartyPersonnel:
        """
        Verify security clearance for third-party personnel.
        
        Args:
            third_party_id: Third-party personnel ID
            org_id: Organization ID (for verification)
            clearance_level: Verified clearance level
            verified_by_user_id: User verifying the clearance
            
        Returns:
            Updated ThirdPartyPersonnel
        """
        try:
            third_party = self.db.query(ThirdPartyPersonnel).filter(
                ThirdPartyPersonnel.id == third_party_id,
                ThirdPartyPersonnel.org_id == org_id,
            ).first()
            
            if not third_party:
                raise ValueError(f"Third-party personnel {third_party_id} not found")
            
            third_party.security_clearance_verified = True
            if clearance_level:
                third_party.security_clearance_level = clearance_level
            
            third_party.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(third_party)
            
            logger.info(
                f"Verified security clearance for third-party {third_party_id}",
                extra={
                    "org_id": org_id,
                    "third_party_id": third_party_id,
                    "event_type": "third_party.clearance_verified",
                }
            )
            
            return third_party
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to verify security clearance: {e}", exc_info=True)
            raise
    
    def complete_background_check(
        self,
        third_party_id: int,
        org_id: int,
        background_check_date: Optional[date] = None,
    ) -> ThirdPartyPersonnel:
        """
        Complete background check for third-party personnel.
        
        Args:
            third_party_id: Third-party personnel ID
            org_id: Organization ID (for verification)
            background_check_date: Background check completion date
            
        Returns:
            Updated ThirdPartyPersonnel
        """
        try:
            third_party = self.db.query(ThirdPartyPersonnel).filter(
                ThirdPartyPersonnel.id == third_party_id,
                ThirdPartyPersonnel.org_id == org_id,
            ).first()
            
            if not third_party:
                raise ValueError(f"Third-party personnel {third_party_id} not found")
            
            third_party.background_check_completed = True
            third_party.background_check_date = background_check_date or date.today()
            third_party.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(third_party)
            
            logger.info(
                f"Completed background check for third-party {third_party_id}",
                extra={
                    "org_id": org_id,
                    "third_party_id": third_party_id,
                    "event_type": "third_party.background_check_completed",
                }
            )
            
            return third_party
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete background check: {e}", exc_info=True)
            raise
    
    def sign_nda(
        self,
        third_party_id: int,
        org_id: int,
        nda_signed_date: Optional[date] = None,
    ) -> ThirdPartyPersonnel:
        """
        Record NDA signature for third-party personnel.
        
        Args:
            third_party_id: Third-party personnel ID
            org_id: Organization ID (for verification)
            nda_signed_date: NDA signing date
            
        Returns:
            Updated ThirdPartyPersonnel
        """
        try:
            third_party = self.db.query(ThirdPartyPersonnel).filter(
                ThirdPartyPersonnel.id == third_party_id,
                ThirdPartyPersonnel.org_id == org_id,
            ).first()
            
            if not third_party:
                raise ValueError(f"Third-party personnel {third_party_id} not found")
            
            third_party.nda_signed = True
            third_party.nda_signed_date = nda_signed_date or date.today()
            third_party.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(third_party)
            
            logger.info(
                f"Recorded NDA signature for third-party {third_party_id}",
                extra={
                    "org_id": org_id,
                    "third_party_id": third_party_id,
                    "event_type": "third_party.nda_signed",
                }
            )
            
            return third_party
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record NDA signature: {e}", exc_info=True)
            raise
    
    def grant_system_access(
        self,
        third_party_id: int,
        org_id: int,
        systems_accessed: List[str],
        access_granted_date: Optional[date] = None,
    ) -> ThirdPartyPersonnel:
        """
        Grant system access to third-party personnel.
        
        Args:
            third_party_id: Third-party personnel ID
            org_id: Organization ID (for verification)
            systems_accessed: List of systems to grant access to
            access_granted_date: Access grant date
            
        Returns:
            Updated ThirdPartyPersonnel
        """
        try:
            third_party = self.db.query(ThirdPartyPersonnel).filter(
                ThirdPartyPersonnel.id == third_party_id,
                ThirdPartyPersonnel.org_id == org_id,
            ).first()
            
            if not third_party:
                raise ValueError(f"Third-party personnel {third_party_id} not found")
            
            third_party.system_access_granted = True
            third_party.systems_accessed = systems_accessed
            third_party.access_granted_date = access_granted_date or date.today()
            third_party.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(third_party)
            
            logger.info(
                f"Granted system access to third-party {third_party_id}",
                extra={
                    "org_id": org_id,
                    "third_party_id": third_party_id,
                    "systems_count": len(systems_accessed),
                    "event_type": "third_party.access_granted",
                }
            )
            
            return third_party
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to grant system access: {e}", exc_info=True)
            raise
    
    def revoke_system_access(
        self,
        third_party_id: int,
        org_id: int,
        access_revoked_date: Optional[date] = None,
    ) -> ThirdPartyPersonnel:
        """
        Revoke system access from third-party personnel.
        
        Args:
            third_party_id: Third-party personnel ID
            org_id: Organization ID (for verification)
            access_revoked_date: Access revocation date
            
        Returns:
            Updated ThirdPartyPersonnel
        """
        try:
            third_party = self.db.query(ThirdPartyPersonnel).filter(
                ThirdPartyPersonnel.id == third_party_id,
                ThirdPartyPersonnel.org_id == org_id,
            ).first()
            
            if not third_party:
                raise ValueError(f"Third-party personnel {third_party_id} not found")
            
            third_party.system_access_granted = False
            third_party.access_revoked_date = access_revoked_date or date.today()
            third_party.systems_accessed = []
            third_party.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(third_party)
            
            logger.info(
                f"Revoked system access from third-party {third_party_id}",
                extra={
                    "org_id": org_id,
                    "third_party_id": third_party_id,
                    "event_type": "third_party.access_revoked",
                }
            )
            
            return third_party
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to revoke system access: {e}", exc_info=True)
            raise
    
    def verify_compliance(
        self,
        third_party_id: int,
        org_id: int,
        verified_by_user_id: int = None,
    ) -> ThirdPartyPersonnel:
        """
        Verify compliance for third-party personnel.
        
        Args:
            third_party_id: Third-party personnel ID
            org_id: Organization ID (for verification)
            verified_by_user_id: User verifying compliance
            
        Returns:
            Updated ThirdPartyPersonnel
        """
        try:
            third_party = self.db.query(ThirdPartyPersonnel).filter(
                ThirdPartyPersonnel.id == third_party_id,
                ThirdPartyPersonnel.org_id == org_id,
            ).first()
            
            if not third_party:
                raise ValueError(f"Third-party personnel {third_party_id} not found")
            
            third_party.compliance_verified = True
            third_party.compliance_verified_date = date.today()
            third_party.compliance_verified_by_user_id = verified_by_user_id
            third_party.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(third_party)
            
            logger.info(
                f"Verified compliance for third-party {third_party_id}",
                extra={
                    "org_id": org_id,
                    "third_party_id": third_party_id,
                    "event_type": "third_party.compliance_verified",
                }
            )
            
            return third_party
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to verify compliance: {e}", exc_info=True)
            raise
    
    def update_status(
        self,
        third_party_id: int,
        org_id: int,
        status: ThirdPartyStatus,
    ) -> ThirdPartyPersonnel:
        """
        Update status of third-party personnel.
        
        Args:
            third_party_id: Third-party personnel ID
            org_id: Organization ID (for verification)
            status: New status
            
        Returns:
            Updated ThirdPartyPersonnel
        """
        try:
            third_party = self.db.query(ThirdPartyPersonnel).filter(
                ThirdPartyPersonnel.id == third_party_id,
                ThirdPartyPersonnel.org_id == org_id,
            ).first()
            
            if not third_party:
                raise ValueError(f"Third-party personnel {third_party_id} not found")
            
            third_party.status = status
            third_party.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(third_party)
            
            return third_party
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update status: {e}", exc_info=True)
            raise
    
    def get_third_party(
        self,
        third_party_id: int,
        org_id: int,
    ) -> Optional[ThirdPartyPersonnel]:
        """Get third-party personnel by ID"""
        return self.db.query(ThirdPartyPersonnel).filter(
            ThirdPartyPersonnel.id == third_party_id,
            ThirdPartyPersonnel.org_id == org_id,
        ).first()
    
    def list_third_party_personnel(
        self,
        org_id: int,
        vendor_name: Optional[str] = None,
        status: Optional[ThirdPartyStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ThirdPartyPersonnel]:
        """
        List third-party personnel for an organization.
        
        Args:
            org_id: Organization ID
            vendor_name: Filter by vendor name (optional)
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of ThirdPartyPersonnel
        """
        query = self.db.query(ThirdPartyPersonnel).filter(
            ThirdPartyPersonnel.org_id == org_id,
        )
        
        if vendor_name:
            query = query.filter(ThirdPartyPersonnel.vendor_name == vendor_name)
        
        if status:
            query = query.filter(ThirdPartyPersonnel.status == status)
        
        return query.order_by(
            ThirdPartyPersonnel.contract_start_date.desc()
        ).limit(limit).offset(offset).all()
    
    def get_expiring_contracts(
        self,
        org_id: int,
        days_ahead: int = 30,
    ) -> List[ThirdPartyPersonnel]:
        """
        Get third-party contracts expiring soon.
        
        Args:
            org_id: Organization ID
            days_ahead: Number of days ahead to check (default 30)
            
        Returns:
            List of ThirdPartyPersonnel with expiring contracts
        """
        from datetime import timedelta
        today = date.today()
        threshold = today + timedelta(days=days_ahead)
        
        return self.db.query(ThirdPartyPersonnel).filter(
            ThirdPartyPersonnel.org_id == org_id,
            ThirdPartyPersonnel.contract_end_date <= threshold,
            ThirdPartyPersonnel.contract_end_date.isnot(None),
            ThirdPartyPersonnel.status == ThirdPartyStatus.ACTIVE,
        ).order_by(ThirdPartyPersonnel.contract_end_date).all()
