"""
Media Sanitization Service for FedRAMP MP-6 Compliance

FedRAMP MP-6: Media Sanitization
- Track sanitization methods
- Verify sanitization
- Generate certificates
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.media_protection import (
    MediaSanitization,
    MediaStorage,
    SanitizationMethod,
    SanitizationStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class MediaSanitizationService:
    """
    Service for managing media sanitization (MP-6).
    
    Implements FedRAMP MP-6 control requirements.
    """
    
    @staticmethod
    def _generate_sanitization_number(db: Session, org_id: int) -> str:
        """Generate unique sanitization number."""
        year = datetime.now(timezone.utc).year
        last_sanitization = db.query(MediaSanitization).filter(
            MediaSanitization.org_id == org_id,
            MediaSanitization.sanitization_number.like(f"SAN-{year}-%"),
        ).order_by(desc(MediaSanitization.sanitization_number)).first()
        
        if last_sanitization:
            try:
                last_num = int(last_sanitization.sanitization_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"SAN-{year}-{next_num:04d}"
    
    @staticmethod
    def _generate_certificate_number(db: Session, org_id: int) -> str:
        """Generate unique certificate number."""
        year = datetime.now(timezone.utc).year
        last_cert = db.query(MediaSanitization).filter(
            MediaSanitization.org_id == org_id,
            MediaSanitization.certificate_number.like(f"CERT-{year}-%"),
        ).order_by(desc(MediaSanitization.certificate_number)).first()
        
        if last_cert:
            try:
                last_num = int(last_cert.certificate_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"CERT-{year}-{next_num:04d}"
    
    @staticmethod
    def create_sanitization(
        db: Session,
        org_id: int,
        media_id: UUID,
        sanitization_method: str,
        sanitization_reason: str,
        sanitized_by_user_id: Optional[int] = None,
        sanitized_by_name: Optional[str] = None,
        sanitized_by_company: Optional[str] = None,
        sanitization_date: Optional[datetime] = None,
    ) -> MediaSanitization:
        """
        Create a media sanitization record (MP-6).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_id: Media ID
            sanitization_method: Sanitization method
            sanitization_reason: Reason for sanitization
            sanitized_by_user_id: User ID performing sanitization
            sanitized_by_name: Name of person performing (if external)
            sanitized_by_company: Company name (if external)
            sanitization_date: Sanitization date
            
        Returns:
            Created MediaSanitization record
        """
        # Verify media exists
        media = db.query(MediaStorage).filter(
            MediaStorage.id == media_id,
            MediaStorage.org_id == org_id,
        ).first()
        
        if not media:
            raise ValueError(f"Media {media_id} not found")
        
        sanitization_number = MediaSanitizationService._generate_sanitization_number(db, org_id)
        
        sanitization = MediaSanitization(
            org_id=org_id,
            media_id=media_id,
            sanitization_number=sanitization_number,
            sanitization_method=sanitization_method,
            sanitization_reason=sanitization_reason,
            sanitization_status=SanitizationStatus.PENDING.value,
            sanitized_by_user_id=sanitized_by_user_id,
            sanitized_by_name=sanitized_by_name,
            sanitized_by_company=sanitized_by_company,
            verified=False,
            sanitization_date=sanitization_date or datetime.now(timezone.utc),
        )
        
        db.add(sanitization)
        db.commit()
        db.refresh(sanitization)
        
        # Log audit event
        MediaSanitizationService._log_audit(
            db=db,
            org_id=org_id,
            user_id=sanitized_by_user_id,
            action="create_media_sanitization",
            resource_type="media_sanitization",
            resource_id=str(sanitization.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_id": str(media_id),
                "sanitization_number": sanitization_number,
                "sanitization_method": sanitization_method,
            },
        )
        
        logger.info(
            "Created media sanitization: sanitization_number=%s, media_id=%s",
            sanitization_number,
            media_id,
        )
        
        return sanitization
    
    @staticmethod
    def mark_completed(
        db: Session,
        sanitization_id: UUID,
        org_id: int,
        completion_date: Optional[datetime] = None,
        sanitization_procedures: Optional[str] = None,
        sanitization_evidence: Optional[dict] = None,
        updated_by_user_id: Optional[int] = None,
    ) -> MediaSanitization:
        """
        Mark sanitization as completed (MP-6).
        
        Args:
            db: Database session
            sanitization_id: Sanitization ID
            org_id: Organization ID
            completion_date: Completion date
            sanitization_procedures: Procedures followed
            sanitization_evidence: Evidence (photos, logs, etc.)
            updated_by_user_id: User ID making update
            
        Returns:
            Updated MediaSanitization record
        """
        sanitization = db.query(MediaSanitization).filter(
            MediaSanitization.id == sanitization_id,
            MediaSanitization.org_id == org_id,
        ).first()
        
        if not sanitization:
            raise ValueError(f"Sanitization {sanitization_id} not found")
        
        sanitization.sanitization_status = SanitizationStatus.COMPLETED.value
        sanitization.completion_date = completion_date or datetime.now(timezone.utc)
        sanitization.sanitization_procedures = sanitization_procedures
        sanitization.sanitization_evidence = sanitization_evidence
        
        db.commit()
        db.refresh(sanitization)
        
        # Log audit event
        MediaSanitizationService._log_audit(
            db=db,
            org_id=org_id,
            user_id=updated_by_user_id,
            action="complete_media_sanitization",
            resource_type="media_sanitization",
            resource_id=str(sanitization_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "sanitization_number": sanitization.sanitization_number,
                "completion_date": sanitization.completion_date.isoformat(),
            },
        )
        
        logger.info("Marked sanitization completed: sanitization_id=%s", sanitization_id)
        
        return sanitization
    
    @staticmethod
    def verify_sanitization(
        db: Session,
        sanitization_id: UUID,
        org_id: int,
        verified_by_user_id: int,
        verification_method: str,
        verification_results: Optional[str] = None,
    ) -> MediaSanitization:
        """
        Verify sanitization (MP-6).
        
        Args:
            db: Database session
            sanitization_id: Sanitization ID
            org_id: Organization ID
            verified_by_user_id: User ID verifying
            verification_method: Verification method
            verification_results: Verification results
            
        Returns:
            Updated MediaSanitization record
        """
        sanitization = db.query(MediaSanitization).filter(
            MediaSanitization.id == sanitization_id,
            MediaSanitization.org_id == org_id,
        ).first()
        
        if not sanitization:
            raise ValueError(f"Sanitization {sanitization_id} not found")
        
        if sanitization.sanitization_status != SanitizationStatus.COMPLETED.value:
            raise ValueError("Sanitization must be completed before verification")
        
        sanitization.verified = True
        sanitization.verified_by_user_id = verified_by_user_id
        sanitization.verified_at = datetime.now(timezone.utc)
        sanitization.verification_method = verification_method
        sanitization.verification_results = verification_results
        sanitization.sanitization_status = SanitizationStatus.VERIFIED.value
        
        db.commit()
        db.refresh(sanitization)
        
        # Log audit event
        MediaSanitizationService._log_audit(
            db=db,
            org_id=org_id,
            user_id=verified_by_user_id,
            action="verify_media_sanitization",
            resource_type="media_sanitization",
            resource_id=str(sanitization_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "sanitization_number": sanitization.sanitization_number,
                "verification_method": verification_method,
            },
        )
        
        logger.info("Verified sanitization: sanitization_id=%s", sanitization_id)
        
        return sanitization
    
    @staticmethod
    def generate_certificate(
        db: Session,
        sanitization_id: UUID,
        org_id: int,
        issued_by_user_id: int,
    ) -> MediaSanitization:
        """
        Generate sanitization certificate (MP-6).
        
        Args:
            db: Database session
            sanitization_id: Sanitization ID
            org_id: Organization ID
            issued_by_user_id: User ID issuing certificate
            
        Returns:
            Updated MediaSanitization record
        """
        sanitization = db.query(MediaSanitization).filter(
            MediaSanitization.id == sanitization_id,
            MediaSanitization.org_id == org_id,
        ).first()
        
        if not sanitization:
            raise ValueError(f"Sanitization {sanitization_id} not found")
        
        if not sanitization.verified:
            raise ValueError("Sanitization must be verified before certificate can be issued")
        
        if not sanitization.certificate_number:
            sanitization.certificate_number = MediaSanitizationService._generate_certificate_number(db, org_id)
        
        sanitization.certificate_issued_at = datetime.now(timezone.utc)
        sanitization.certificate_issued_by_user_id = issued_by_user_id
        
        db.commit()
        db.refresh(sanitization)
        
        # Log audit event
        MediaSanitizationService._log_audit(
            db=db,
            org_id=org_id,
            user_id=issued_by_user_id,
            action="generate_sanitization_certificate",
            resource_type="media_sanitization",
            resource_id=str(sanitization_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "sanitization_number": sanitization.sanitization_number,
                "certificate_number": sanitization.certificate_number,
            },
        )
        
        logger.info(
            "Generated sanitization certificate: sanitization_id=%s, cert=%s",
            sanitization_id,
            sanitization.certificate_number,
        )
        
        return sanitization
    
    @staticmethod
    def list_sanitizations(
        db: Session,
        org_id: int,
        media_id: Optional[UUID] = None,
        sanitization_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MediaSanitization]:
        """
        List media sanitization records (MP-6).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_id: Optional media ID filter
            sanitization_status: Optional status filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of MediaSanitization records
        """
        query = db.query(MediaSanitization).filter(
            MediaSanitization.org_id == org_id,
        )
        
        if media_id:
            query = query.filter(MediaSanitization.media_id == media_id)
        
        if sanitization_status:
            query = query.filter(MediaSanitization.sanitization_status == sanitization_status)
        
        return query.order_by(desc(MediaSanitization.sanitization_date)).limit(limit).offset(offset).all()
    
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
        """Log media sanitization audit event."""
        try:
            audit_log = ComprehensiveAuditLog(
                org_id=org_id,
                user_id=user_id,
                event_type=AuditEventType.DATA_MODIFICATION.value,
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
