"""
Media Marking Service for FedRAMP MP-3 Compliance

FedRAMP MP-3: Media Marking
- Mark media with classification labels
- Validate markings
- Track marking lifecycle
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.media_protection import (
    MediaMarking,
    MediaStorage,
    ClassificationLevel,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class MediaMarkingService:
    """
    Service for managing media markings (MP-3).
    
    Implements FedRAMP MP-3 control requirements.
    """
    
    @staticmethod
    def create_marking(
        db: Session,
        org_id: int,
        media_id: UUID,
        classification_level: str,
        classification_label: str,
        classification_marking: Optional[str] = None,
        marked_by_user_id: Optional[int] = None,
        marked_by_email: Optional[str] = None,
    ) -> MediaMarking:
        """
        Create a media marking (MP-3).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_id: Media ID
            classification_level: Classification level
            classification_label: Human-readable label
            classification_marking: Full marking text
            marked_by_user_id: User ID creating marking
            marked_by_email: User email (denormalized)
            
        Returns:
            Created MediaMarking record
        """
        # Verify media exists and belongs to org
        media = db.query(MediaStorage).filter(
            MediaStorage.id == media_id,
            MediaStorage.org_id == org_id,
        ).first()
        
        if not media:
            raise ValueError(f"Media {media_id} not found")
        
        # Supersede existing active markings
        db.query(MediaMarking).filter(
            MediaMarking.media_id == media_id,
            MediaMarking.org_id == org_id,
            MediaMarking.superseded_at.is_(None),
        ).update({
            "superseded_at": datetime.now(timezone.utc),
        })
        
        marking = MediaMarking(
            org_id=org_id,
            media_id=media_id,
            classification_level=classification_level,
            classification_label=classification_label,
            classification_marking=classification_marking,
            marked_by_user_id=marked_by_user_id,
            marked_by_email=marked_by_email,
            validated=False,
            created_at=datetime.now(timezone.utc),
        )
        
        db.add(marking)
        db.commit()
        db.refresh(marking)
        
        # Log audit event
        MediaMarkingService._log_audit(
            db=db,
            org_id=org_id,
            user_id=marked_by_user_id,
            action="create_media_marking",
            resource_type="media_marking",
            resource_id=str(marking.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_id": str(media_id),
                "media_identifier": media.media_identifier,
                "classification_level": classification_level,
                "classification_label": classification_label,
            },
        )
        
        logger.info(
            "Created media marking: media_id=%s, classification=%s",
            media_id,
            classification_level,
        )
        
        return marking
    
    @staticmethod
    def validate_marking(
        db: Session,
        marking_id: UUID,
        org_id: int,
        validated_by_user_id: Optional[int] = None,
    ) -> MediaMarking:
        """
        Validate a media marking (MP-3).
        
        Args:
            db: Database session
            marking_id: Marking ID
            org_id: Organization ID
            validated_by_user_id: User ID validating
            
        Returns:
            Updated MediaMarking record
        """
        marking = db.query(MediaMarking).filter(
            MediaMarking.id == marking_id,
            MediaMarking.org_id == org_id,
        ).first()
        
        if not marking:
            raise ValueError(f"Marking {marking_id} not found")
        
        marking.validated = True
        marking.validated_by_user_id = validated_by_user_id
        marking.validated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(marking)
        
        # Log audit event
        MediaMarkingService._log_audit(
            db=db,
            org_id=org_id,
            user_id=validated_by_user_id,
            action="validate_media_marking",
            resource_type="media_marking",
            resource_id=str(marking_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_id": str(marking.media_id),
                "classification_level": marking.classification_level,
            },
        )
        
        logger.info("Validated media marking: marking_id=%s", marking_id)
        
        return marking
    
    @staticmethod
    def get_active_marking(
        db: Session,
        media_id: UUID,
        org_id: int,
    ) -> Optional[MediaMarking]:
        """
        Get active marking for media (MP-3).
        
        Args:
            db: Database session
            media_id: Media ID
            org_id: Organization ID
            
        Returns:
            Active MediaMarking or None
        """
        return db.query(MediaMarking).filter(
            MediaMarking.media_id == media_id,
            MediaMarking.org_id == org_id,
            MediaMarking.superseded_at.is_(None),
        ).order_by(desc(MediaMarking.created_at)).first()
    
    @staticmethod
    def list_markings(
        db: Session,
        org_id: int,
        media_id: Optional[UUID] = None,
        classification_level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MediaMarking]:
        """
        List media markings (MP-3).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_id: Optional media ID filter
            classification_level: Optional classification filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of MediaMarking records
        """
        query = db.query(MediaMarking).filter(
            MediaMarking.org_id == org_id,
        )
        
        if media_id:
            query = query.filter(MediaMarking.media_id == media_id)
        
        if classification_level:
            query = query.filter(MediaMarking.classification_level == classification_level)
        
        return query.order_by(desc(MediaMarking.created_at)).limit(limit).offset(offset).all()
    
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
        """Log media marking audit event."""
        try:
            audit_log = ComprehensiveAuditLog(
                org_id=org_id,
                user_id=user_id,
                event_type=AuditEventType.CONFIGURATION_CHANGE.value,
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
