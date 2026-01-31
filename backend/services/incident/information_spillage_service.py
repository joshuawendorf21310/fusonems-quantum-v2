"""
IR-9: Information Spillage Response Service for FedRAMP Compliance

Provides comprehensive information spillage response capabilities:
- Spillage detection
- Containment procedures
- Notification workflow
- Cleanup verification
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from core.logger import logger
from models.incident import (
    InformationSpillage,
    SpillageStatus,
)
from models.user import User
from utils.audit import record_audit


class InformationSpillageService:
    """Service for managing information spillage incidents per FedRAMP IR-9 requirements"""

    @staticmethod
    def generate_spillage_number(org_id: int) -> str:
        """Generate unique spillage number"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        from uuid import uuid4
        random_part = str(uuid4())[:8].upper()
        return f"SPL-{org_id}-{timestamp}-{random_part}"

    @staticmethod
    def create_spillage(
        db: Session,
        org_id: int,
        title: str,
        description: str,
        classification: str,
        sensitivity_level: str = "moderate",
        data_type: Optional[str] = None,
        affected_systems: Optional[List[str]] = None,
        affected_data_elements: Optional[List[str]] = None,
        estimated_records_affected: Optional[int] = None,
        detected_by_user_id: Optional[int] = None,
        detected_by_system: bool = False,
        detection_method: Optional[str] = None,
        request=None,
    ) -> InformationSpillage:
        """Create a new information spillage incident"""
        spillage_number = InformationSpillageService.generate_spillage_number(org_id)
        
        spillage = InformationSpillage(
            org_id=org_id,
            spillage_number=spillage_number,
            title=title,
            description=description,
            classification=classification,
            sensitivity_level=sensitivity_level,
            data_type=data_type,
            affected_systems=affected_systems or [],
            affected_data_elements=affected_data_elements or [],
            estimated_records_affected=estimated_records_affected,
            detected_by_user_id=detected_by_user_id,
            detected_by_system=detected_by_system,
            detection_method=detection_method,
            status=SpillageStatus.DETECTED.value,
        )
        
        db.add(spillage)
        db.commit()
        db.refresh(spillage)
        
        # Audit log
        if request and detected_by_user_id:
            try:
                user = db.query(User).filter(User.id == detected_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="information_spillage_detected",
                        resource="information_spillage",
                        outcome="Success",
                        classification=classification,
                        reason_code="IR9_SPILLAGE_DETECTED",
                        after_state={
                            "spillage_id": str(spillage.id),
                            "spillage_number": spillage_number,
                            "classification": classification,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for spillage detection: {e}", exc_info=True)
        
        logger.info(
            f"Information spillage detected: {spillage_number}, "
            f"classification={classification}, sensitivity={sensitivity_level}"
        )
        return spillage

    @staticmethod
    def contain_spillage(
        db: Session,
        spillage_id: UUID,
        contained_by_user_id: int,
        containment_procedures: str,
        containment_actions_taken: List[str],
        request=None,
    ) -> InformationSpillage:
        """Contain an information spillage"""
        spillage = db.query(InformationSpillage).filter(
            InformationSpillage.id == spillage_id,
        ).first()
        
        if not spillage:
            raise ValueError(f"Spillage not found: {spillage_id}")
        
        spillage.status = SpillageStatus.CONTAINED.value
        spillage.contained_at = datetime.now(timezone.utc)
        spillage.containment_procedures = containment_procedures
        spillage.containment_actions_taken = containment_actions_taken
        
        db.commit()
        db.refresh(spillage)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == contained_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="information_spillage_contained",
                        resource="information_spillage",
                        outcome="Success",
                        classification=spillage.classification,
                        reason_code="IR9_SPILLAGE_CONTAINED",
                        after_state={
                            "spillage_id": str(spillage_id),
                            "containment_actions_count": len(containment_actions_taken),
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for containment: {e}", exc_info=True)
        
        logger.info(f"Information spillage contained: spillage_id={spillage_id}")
        return spillage

    @staticmethod
    def send_notifications(
        db: Session,
        spillage_id: UUID,
        notified_parties: List[str],
        notification_details: Optional[Dict[str, str]] = None,
        sent_by_user_id: Optional[int] = None,
        request=None,
    ) -> InformationSpillage:
        """Record spillage notifications sent"""
        spillage = db.query(InformationSpillage).filter(
            InformationSpillage.id == spillage_id,
        ).first()
        
        if not spillage:
            raise ValueError(f"Spillage not found: {spillage_id}")
        
        now = datetime.now(timezone.utc)
        notifications_sent = spillage.notifications_sent or []
        notification_timestamps = spillage.notification_timestamps or {}
        
        for party in notified_parties:
            if party not in notifications_sent:
                notifications_sent.append(party)
            notification_timestamps[party] = now.isoformat()
        
        spillage.notifications_sent = notifications_sent
        spillage.notified_parties = notified_parties
        spillage.notification_timestamps = notification_timestamps
        
        db.commit()
        db.refresh(spillage)
        
        # Audit log
        if request and sent_by_user_id:
            try:
                user = db.query(User).filter(User.id == sent_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="spillage_notifications_sent",
                        resource="information_spillage",
                        outcome="Success",
                        classification=spillage.classification,
                        reason_code="IR9_NOTIFICATIONS_SENT",
                        after_state={
                            "spillage_id": str(spillage_id),
                            "notified_parties_count": len(notified_parties),
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for notifications: {e}", exc_info=True)
        
        logger.info(
            f"Spillage notifications sent: spillage_id={spillage_id}, "
            f"parties={len(notified_parties)}"
        )
        return spillage

    @staticmethod
    def start_cleanup(
        db: Session,
        spillage_id: UUID,
        cleanup_procedures: str,
        started_by_user_id: int,
        request=None,
    ) -> InformationSpillage:
        """Start cleanup process"""
        spillage = db.query(InformationSpillage).filter(
            InformationSpillage.id == spillage_id,
        ).first()
        
        if not spillage:
            raise ValueError(f"Spillage not found: {spillage_id}")
        
        spillage.status = SpillageStatus.CLEANUP_IN_PROGRESS.value
        spillage.cleanup_started_at = datetime.now(timezone.utc)
        spillage.cleanup_procedures = cleanup_procedures
        
        db.commit()
        db.refresh(spillage)
        
        logger.info(f"Spillage cleanup started: spillage_id={spillage_id}")
        return spillage

    @staticmethod
    def complete_cleanup(
        db: Session,
        spillage_id: UUID,
        cleanup_actions_taken: List[str],
        completed_by_user_id: int,
        request=None,
    ) -> InformationSpillage:
        """Complete cleanup process"""
        spillage = db.query(InformationSpillage).filter(
            InformationSpillage.id == spillage_id,
        ).first()
        
        if not spillage:
            raise ValueError(f"Spillage not found: {spillage_id}")
        
        spillage.cleanup_completed_at = datetime.now(timezone.utc)
        spillage.cleanup_actions_taken = cleanup_actions_taken
        
        db.commit()
        db.refresh(spillage)
        
        logger.info(f"Spillage cleanup completed: spillage_id={spillage_id}")
        return spillage

    @staticmethod
    def verify_cleanup(
        db: Session,
        spillage_id: UUID,
        verified_by_user_id: int,
        verification_method: str,
        verification_results: str,
        verification_passed: bool,
        request=None,
    ) -> InformationSpillage:
        """Verify cleanup completion"""
        spillage = db.query(InformationSpillage).filter(
            InformationSpillage.id == spillage_id,
        ).first()
        
        if not spillage:
            raise ValueError(f"Spillage not found: {spillage_id}")
        
        spillage.status = SpillageStatus.VERIFIED.value if verification_passed else SpillageStatus.CLEANUP_IN_PROGRESS.value
        spillage.verified_at = datetime.now(timezone.utc)
        spillage.verified_by_user_id = verified_by_user_id
        spillage.verification_method = verification_method
        spillage.verification_results = verification_results
        spillage.verification_passed = verification_passed
        
        if verification_passed:
            spillage.resolved_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(spillage)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == verified_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="spillage_cleanup_verified",
                        resource="information_spillage",
                        outcome="Success" if verification_passed else "Failed",
                        classification=spillage.classification,
                        reason_code="IR9_CLEANUP_VERIFIED",
                        after_state={
                            "spillage_id": str(spillage_id),
                            "verification_passed": verification_passed,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for verification: {e}", exc_info=True)
        
        logger.info(
            f"Spillage cleanup verified: spillage_id={spillage_id}, "
            f"passed={verification_passed}"
        )
        return spillage

    @staticmethod
    def close_spillage(
        db: Session,
        spillage_id: UUID,
        closed_by_user_id: int,
        lessons_learned: Optional[str] = None,
        request=None,
    ) -> InformationSpillage:
        """Close a spillage incident"""
        spillage = db.query(InformationSpillage).filter(
            InformationSpillage.id == spillage_id,
        ).first()
        
        if not spillage:
            raise ValueError(f"Spillage not found: {spillage_id}")
        
        if spillage.status != SpillageStatus.VERIFIED.value:
            raise ValueError("Spillage must be verified before closing")
        
        spillage.status = SpillageStatus.CLOSED.value
        spillage.closed_at = datetime.now(timezone.utc)
        if lessons_learned:
            spillage.lessons_learned = lessons_learned
        
        db.commit()
        db.refresh(spillage)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == closed_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="information_spillage_closed",
                        resource="information_spillage",
                        outcome="Success",
                        classification=spillage.classification,
                        reason_code="IR9_SPILLAGE_CLOSED",
                        after_state={
                            "spillage_id": str(spillage_id),
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for closure: {e}", exc_info=True)
        
        logger.info(f"Information spillage closed: spillage_id={spillage_id}")
        return spillage

    @staticmethod
    def get_spillage(
        db: Session,
        spillage_id: UUID,
        org_id: Optional[int] = None,
    ) -> Optional[InformationSpillage]:
        """Get spillage by ID"""
        query = db.query(InformationSpillage).filter(
            InformationSpillage.id == spillage_id,
        )
        
        if org_id:
            query = query.filter(InformationSpillage.org_id == org_id)
        
        return query.first()

    @staticmethod
    def list_spillages(
        db: Session,
        org_id: int,
        status: Optional[SpillageStatus] = None,
        classification: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InformationSpillage]:
        """List spillages with filters"""
        query = db.query(InformationSpillage).filter(
            InformationSpillage.org_id == org_id,
        )
        
        if status:
            query = query.filter(InformationSpillage.status == status.value)
        
        if classification:
            query = query.filter(InformationSpillage.classification == classification)
        
        return query.order_by(desc(InformationSpillage.detected_at)).limit(limit).offset(offset).all()
