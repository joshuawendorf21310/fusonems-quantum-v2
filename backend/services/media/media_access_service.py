"""
Media Access Service for FedRAMP MP-2 Compliance

FedRAMP MP-2: Media Access
- Control access to media
- Track access authorization
- Log all access events
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, or_

from core.logger import logger
from models.media_protection import (
    MediaAccess,
    MediaStorage,
    AccessStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class MediaAccessService:
    """
    Service for managing media access (MP-2).
    
    Implements FedRAMP MP-2 control requirements.
    """
    
    @staticmethod
    def grant_access(
        db: Session,
        org_id: int,
        media_id: UUID,
        user_id: int,
        user_email: Optional[str] = None,
        access_purpose: str = "",
        access_level: str = "read",
        authorized_by_user_id: Optional[int] = None,
        authorization_reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> MediaAccess:
        """
        Grant access to media (MP-2).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_id: Media ID
            user_id: User ID to grant access to
            user_email: User email (denormalized)
            access_purpose: Purpose for access
            access_level: Access level (read, write, full)
            authorized_by_user_id: User ID authorizing access
            authorization_reason: Reason for authorization
            expires_at: When access expires
            
        Returns:
            Created MediaAccess record
        """
        # Verify media exists and belongs to org
        media = db.query(MediaStorage).filter(
            MediaStorage.id == media_id,
            MediaStorage.org_id == org_id,
        ).first()
        
        if not media:
            raise ValueError(f"Media {media_id} not found")
        
        # Check for existing active access
        existing = db.query(MediaAccess).filter(
            MediaAccess.media_id == media_id,
            MediaAccess.user_id == user_id,
            MediaAccess.access_status == AccessStatus.GRANTED.value,
            or_(
                MediaAccess.expires_at.is_(None),
                MediaAccess.expires_at > datetime.now(timezone.utc),
            ),
        ).first()
        
        if existing:
            raise ValueError(f"User {user_id} already has active access to media {media_id}")
        
        access = MediaAccess(
            org_id=org_id,
            media_id=media_id,
            user_id=user_id,
            user_email=user_email,
            access_status=AccessStatus.GRANTED.value,
            access_purpose=access_purpose,
            access_level=access_level,
            authorized_by_user_id=authorized_by_user_id,
            authorization_reason=authorization_reason,
            granted_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        
        db.add(access)
        db.commit()
        db.refresh(access)
        
        # Log audit event
        MediaAccessService._log_audit(
            db=db,
            org_id=org_id,
            user_id=authorized_by_user_id,
            action="grant_media_access",
            resource_type="media_access",
            resource_id=str(access.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_id": str(media_id),
                "media_identifier": media.media_identifier,
                "granted_to_user_id": user_id,
                "access_level": access_level,
                "expires_at": expires_at.isoformat() if expires_at else None,
            },
        )
        
        logger.info(
            "Granted media access: media_id=%s, user_id=%d, access_level=%s",
            media_id,
            user_id,
            access_level,
        )
        
        return access
    
    @staticmethod
    def revoke_access(
        db: Session,
        access_id: UUID,
        org_id: int,
        revoked_by_user_id: Optional[int] = None,
        revocation_reason: Optional[str] = None,
    ) -> MediaAccess:
        """
        Revoke media access (MP-2).
        
        Args:
            db: Database session
            access_id: Access record ID
            org_id: Organization ID
            revoked_by_user_id: User ID revoking access
            revocation_reason: Reason for revocation
            
        Returns:
            Updated MediaAccess record
        """
        access = db.query(MediaAccess).filter(
            MediaAccess.id == access_id,
            MediaAccess.org_id == org_id,
        ).first()
        
        if not access:
            raise ValueError(f"Access record {access_id} not found")
        
        if access.access_status == AccessStatus.REVOKED.value:
            raise ValueError(f"Access already revoked")
        
        access.access_status = AccessStatus.REVOKED.value
        access.revoked_at = datetime.now(timezone.utc)
        access.revoked_by_user_id = revoked_by_user_id
        access.revocation_reason = revocation_reason
        
        db.commit()
        db.refresh(access)
        
        # Log audit event
        MediaAccessService._log_audit(
            db=db,
            org_id=org_id,
            user_id=revoked_by_user_id,
            action="revoke_media_access",
            resource_type="media_access",
            resource_id=str(access_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_id": str(access.media_id),
                "revoked_user_id": access.user_id,
                "revocation_reason": revocation_reason,
            },
        )
        
        logger.info(
            "Revoked media access: access_id=%s, user_id=%d",
            access_id,
            access.user_id,
        )
        
        return access
    
    @staticmethod
    def list_access(
        db: Session,
        org_id: int,
        media_id: Optional[UUID] = None,
        user_id: Optional[int] = None,
        access_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MediaAccess]:
        """
        List media access records (MP-2).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_id: Optional media ID filter
            user_id: Optional user ID filter
            access_status: Optional status filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of MediaAccess records
        """
        query = db.query(MediaAccess).filter(
            MediaAccess.org_id == org_id,
        )
        
        if media_id:
            query = query.filter(MediaAccess.media_id == media_id)
        
        if user_id:
            query = query.filter(MediaAccess.user_id == user_id)
        
        if access_status:
            query = query.filter(MediaAccess.access_status == access_status)
        
        return query.order_by(desc(MediaAccess.granted_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def check_access(
        db: Session,
        media_id: UUID,
        user_id: int,
        org_id: int,
    ) -> bool:
        """
        Check if user has active access to media (MP-2).
        
        Args:
            db: Database session
            media_id: Media ID
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            True if user has active access, False otherwise
        """
        access = db.query(MediaAccess).filter(
            MediaAccess.media_id == media_id,
            MediaAccess.user_id == user_id,
            MediaAccess.org_id == org_id,
            MediaAccess.access_status == AccessStatus.GRANTED.value,
            or_(
                MediaAccess.expires_at.is_(None),
                MediaAccess.expires_at > datetime.now(timezone.utc),
            ),
        ).first()
        
        return access is not None
    
    @staticmethod
    def _log_audit(
        db: Session,
        org_id: int,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str,
        metadata: Optional[dict] = None,
    ):
        """Log media access audit event."""
        try:
            audit_log = ComprehensiveAuditLog(
                org_id=org_id,
                user_id=user_id,
                event_type=AuditEventType.AUTHORIZATION.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                metadata=metadata,
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error("Failed to log audit event: %s", e)
            db.rollback()
