"""
PE-2: Physical Access Authorization Service
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.physical_environmental import (
    PhysicalAccessAuthorization,
    AuthorizationStatus,
)
from core.logger import logger


class PhysicalAccessAuthorizationService:
    """Service for managing physical access authorizations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_authorization(
        self,
        org_id: int,
        user_id: int,
        authorization_type: str,
        access_level: str,
        authorized_areas: List[str],
        badge_type: str,
        credential_type: str,
        credential_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        justification: Optional[str] = None,
        requested_by: Optional[int] = None,
    ) -> PhysicalAccessAuthorization:
        """Create a new physical access authorization request"""
        
        badge_number = self._generate_badge_number(org_id)
        
        authorization = PhysicalAccessAuthorization(
            org_id=org_id,
            user_id=user_id,
            authorization_type=authorization_type,
            access_level=access_level,
            authorized_areas=authorized_areas,
            badge_number=badge_number,
            badge_type=badge_type,
            credential_type=credential_type,
            credential_id=credential_id,
            expires_at=expires_at,
            justification=justification,
            requested_by=requested_by,
            status=AuthorizationStatus.PENDING.value,
            requested_at=datetime.utcnow(),
        )
        
        self.db.add(authorization)
        self.db.commit()
        self.db.refresh(authorization)
        
        logger.info(f"Created physical access authorization {authorization.id} for user {user_id}")
        return authorization
    
    def approve_authorization(
        self,
        authorization_id: int,
        approved_by: int,
        badge_number: Optional[str] = None,
    ) -> PhysicalAccessAuthorization:
        """Approve a physical access authorization"""
        
        authorization = self.db.query(PhysicalAccessAuthorization).filter(
            PhysicalAccessAuthorization.id == authorization_id
        ).first()
        
        if not authorization:
            raise ValueError(f"Authorization {authorization_id} not found")
        
        if authorization.status != AuthorizationStatus.PENDING.value:
            raise ValueError(f"Authorization {authorization_id} is not pending")
        
        authorization.status = AuthorizationStatus.APPROVED.value
        authorization.approved_by = approved_by
        authorization.approved_at = datetime.utcnow()
        
        if badge_number:
            authorization.badge_number = badge_number
        
        authorization.next_review_due = datetime.utcnow() + timedelta(days=authorization.review_frequency_days)
        
        self.db.commit()
        self.db.refresh(authorization)
        
        logger.info(f"Approved physical access authorization {authorization_id}")
        return authorization
    
    def revoke_authorization(
        self,
        authorization_id: int,
        revoked_by: int,
        reason: str,
    ) -> PhysicalAccessAuthorization:
        """Revoke a physical access authorization"""
        
        authorization = self.db.query(PhysicalAccessAuthorization).filter(
            PhysicalAccessAuthorization.id == authorization_id
        ).first()
        
        if not authorization:
            raise ValueError(f"Authorization {authorization_id} not found")
        
        authorization.status = AuthorizationStatus.REVOKED.value
        authorization.revoked_by = revoked_by
        authorization.revoked_at = datetime.utcnow()
        authorization.revocation_reason = reason
        
        self.db.commit()
        self.db.refresh(authorization)
        
        logger.info(f"Revoked physical access authorization {authorization_id}")
        return authorization
    
    def get_user_authorizations(
        self,
        org_id: int,
        user_id: int,
        include_expired: bool = False,
    ) -> List[PhysicalAccessAuthorization]:
        """Get all authorizations for a user"""
        
        query = self.db.query(PhysicalAccessAuthorization).filter(
            and_(
                PhysicalAccessAuthorization.org_id == org_id,
                PhysicalAccessAuthorization.user_id == user_id,
            )
        )
        
        if not include_expired:
            query = query.filter(
                or_(
                    PhysicalAccessAuthorization.expires_at.is_(None),
                    PhysicalAccessAuthorization.expires_at > datetime.utcnow(),
                )
            ).filter(
                PhysicalAccessAuthorization.status.in_([
                    AuthorizationStatus.APPROVED.value,
                    AuthorizationStatus.PENDING.value,
                ])
            )
        
        return query.all()
    
    def get_expiring_authorizations(
        self,
        org_id: int,
        days_ahead: int = 30,
    ) -> List[PhysicalAccessAuthorization]:
        """Get authorizations expiring within specified days"""
        
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return self.db.query(PhysicalAccessAuthorization).filter(
            and_(
                PhysicalAccessAuthorization.org_id == org_id,
                PhysicalAccessAuthorization.status == AuthorizationStatus.APPROVED.value,
                PhysicalAccessAuthorization.expires_at.isnot(None),
                PhysicalAccessAuthorization.expires_at <= cutoff_date,
                PhysicalAccessAuthorization.expires_at > datetime.utcnow(),
            )
        ).all()
    
    def get_due_for_review(
        self,
        org_id: int,
    ) -> List[PhysicalAccessAuthorization]:
        """Get authorizations due for review"""
        
        return self.db.query(PhysicalAccessAuthorization).filter(
            and_(
                PhysicalAccessAuthorization.org_id == org_id,
                PhysicalAccessAuthorization.status == AuthorizationStatus.APPROVED.value,
                or_(
                    PhysicalAccessAuthorization.next_review_due.is_(None),
                    PhysicalAccessAuthorization.next_review_due <= datetime.utcnow(),
                ),
            )
        ).all()
    
    def review_authorization(
        self,
        authorization_id: int,
        reviewed_by: int,
        continue_authorization: bool,
        notes: Optional[str] = None,
    ) -> PhysicalAccessAuthorization:
        """Perform authorization review"""
        
        authorization = self.db.query(PhysicalAccessAuthorization).filter(
            PhysicalAccessAuthorization.id == authorization_id
        ).first()
        
        if not authorization:
            raise ValueError(f"Authorization {authorization_id} not found")
        
        authorization.last_reviewed_at = datetime.utcnow()
        
        if continue_authorization:
            authorization.next_review_due = datetime.utcnow() + timedelta(days=authorization.review_frequency_days)
        else:
            authorization.status = AuthorizationStatus.EXPIRED.value
            authorization.expires_at = datetime.utcnow()
        
        if notes:
            authorization.metadata = authorization.metadata or {}
            authorization.metadata['review_notes'] = notes
        
        self.db.commit()
        self.db.refresh(authorization)
        
        logger.info(f"Reviewed physical access authorization {authorization_id}")
        return authorization
    
    def _generate_badge_number(self, org_id: int) -> str:
        """Generate a unique badge number"""
        import random
        import string
        
        while True:
            badge_number = f"BADGE-{org_id}-{''.join(random.choices(string.digits, k=6))}"
            
            existing = self.db.query(PhysicalAccessAuthorization).filter(
                PhysicalAccessAuthorization.badge_number == badge_number
            ).first()
            
            if not existing:
                return badge_number
    
    def get_authorization_statistics(
        self,
        org_id: int,
    ) -> Dict[str, Any]:
        """Get authorization statistics for dashboard"""
        
        total = self.db.query(PhysicalAccessAuthorization).filter(
            PhysicalAccessAuthorization.org_id == org_id
        ).count()
        
        approved = self.db.query(PhysicalAccessAuthorization).filter(
            and_(
                PhysicalAccessAuthorization.org_id == org_id,
                PhysicalAccessAuthorization.status == AuthorizationStatus.APPROVED.value,
            )
        ).count()
        
        pending = self.db.query(PhysicalAccessAuthorization).filter(
            and_(
                PhysicalAccessAuthorization.org_id == org_id,
                PhysicalAccessAuthorization.status == AuthorizationStatus.PENDING.value,
            )
        ).count()
        
        expiring_soon = len(self.get_expiring_authorizations(org_id, days_ahead=30))
        due_for_review = len(self.get_due_for_review(org_id))
        
        return {
            "total_authorizations": total,
            "approved": approved,
            "pending": pending,
            "expiring_soon": expiring_soon,
            "due_for_review": due_for_review,
        }
