"""
Information Handling & Retention Service for FedRAMP SI-12 Compliance

This service provides:
- Retention policies
- Automated purging
- Legal hold management

FedRAMP SI-12: Information Handling & Retention
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from models.system_integrity import (
    InformationRetentionPolicy,
    LegalHold,
    DataPurgeRecord,
    RetentionPolicyStatus,
    LegalHoldStatus,
)
from utils.logger import logger


class InformationHandlingService:
    """
    Service for information handling and retention management.
    
    FedRAMP SI-12: Information Handling & Retention
    """
    
    def __init__(self, db: Session):
        """
        Initialize information handling service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_retention_policy(
        self,
        policy_id: str,
        policy_name: str,
        data_type: str,
        retention_period_days: int,
        auto_purge_enabled: bool = True,
        purge_schedule: Optional[str] = None,
        organization_id: Optional[int] = None,
        compliance_requirements: Optional[List[str]] = None,
    ) -> InformationRetentionPolicy:
        """
        Create a new retention policy.
        
        Args:
            policy_id: Unique policy identifier
            policy_name: Policy name
            data_type: Type of data (e.g., "audit_log", "user_data")
            retention_period_days: Retention period in days
            auto_purge_enabled: Whether to enable automatic purging
            purge_schedule: Purge schedule ("daily", "weekly", "monthly")
            organization_id: Organization ID (if org-specific)
            compliance_requirements: List of compliance requirements
            
        Returns:
            Created InformationRetentionPolicy
        """
        policy = InformationRetentionPolicy(
            policy_id=policy_id,
            policy_name=policy_name,
            data_type=data_type,
            retention_period_days=retention_period_days,
            auto_purge_enabled=auto_purge_enabled,
            purge_schedule=purge_schedule or "daily",
            organization_id=organization_id,
            compliance_requirements=compliance_requirements or [],
            status=RetentionPolicyStatus.ACTIVE.value,
            effective_date=datetime.utcnow(),
        )
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        logger.info(
            f"Retention policy created: {policy_id}",
            extra={
                "policy_id": policy_id,
                "data_type": data_type,
                "retention_period_days": retention_period_days,
                "event_type": "retention_policy.created",
            }
        )
        
        return policy
    
    def create_legal_hold(
        self,
        hold_id: str,
        case_name: str,
        data_types: List[str],
        created_by: str,
        organization_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None,
        date_range_start: Optional[datetime] = None,
        date_range_end: Optional[datetime] = None,
        case_number: Optional[str] = None,
        legal_counsel: Optional[str] = None,
        court_order_number: Optional[str] = None,
    ) -> LegalHold:
        """
        Create a legal hold to prevent data purging.
        
        Args:
            hold_id: Unique hold identifier
            case_name: Case name
            data_types: List of data types covered
            created_by: User who created the hold
            organization_id: Organization ID
            user_ids: Specific user IDs if applicable
            date_range_start: Start date range
            date_range_end: End date range
            case_number: Case number
            legal_counsel: Legal counsel name
            court_order_number: Court order number
            
        Returns:
            Created LegalHold
        """
        hold = LegalHold(
            hold_id=hold_id,
            case_name=case_name,
            case_number=case_number,
            data_types=data_types,
            organization_id=organization_id,
            user_ids=user_ids,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            legal_counsel=legal_counsel,
            court_order_number=court_order_number,
            court_order_date=datetime.utcnow() if court_order_number else None,
            status=LegalHoldStatus.ACTIVE.value,
            created_by=created_by,
        )
        
        self.db.add(hold)
        self.db.commit()
        self.db.refresh(hold)
        
        logger.warning(
            f"Legal hold created: {hold_id}",
            extra={
                "hold_id": hold_id,
                "case_name": case_name,
                "data_types": data_types,
                "event_type": "legal_hold.created",
            }
        )
        
        return hold
    
    def release_legal_hold(
        self,
        hold_id: str,
        released_by: str,
        release_reason: str,
    ) -> LegalHold:
        """
        Release a legal hold.
        
        Args:
            hold_id: Hold identifier
            released_by: User who released the hold
            release_reason: Reason for release
            
        Returns:
            Updated LegalHold
        """
        hold = self.db.query(LegalHold).filter(
            LegalHold.hold_id == hold_id
        ).first()
        
        if not hold:
            raise ValueError(f"Legal hold not found: {hold_id}")
        
        hold.status = LegalHoldStatus.RELEASED.value
        hold.released_at = datetime.utcnow()
        hold.released_by = released_by
        hold.release_reason = release_reason
        
        self.db.commit()
        self.db.refresh(hold)
        
        logger.info(
            f"Legal hold released: {hold_id}",
            extra={
                "hold_id": hold_id,
                "released_by": released_by,
                "event_type": "legal_hold.released",
            }
        )
        
        return hold
    
    def execute_purge(
        self,
        policy_id: str,
        data_type: str,
        executed_by: str,
        date_range_start: Optional[datetime] = None,
        date_range_end: Optional[datetime] = None,
        organization_id: Optional[int] = None,
    ) -> DataPurgeRecord:
        """
        Execute data purge according to retention policy.
        
        Args:
            policy_id: Policy identifier
            data_type: Type of data to purge
            executed_by: User who executed the purge
            date_range_start: Start date range
            date_range_end: End date range
            organization_id: Organization ID
            
        Returns:
            DataPurgeRecord
        """
        policy = self.db.query(InformationRetentionPolicy).filter(
            InformationRetentionPolicy.policy_id == policy_id
        ).first()
        
        if not policy:
            raise ValueError(f"Retention policy not found: {policy_id}")
        
        # Calculate purge cutoff date
        if not date_range_end:
            date_range_end = datetime.utcnow()
        
        if not date_range_start:
            date_range_start = date_range_end - timedelta(days=policy.retention_period_days)
        
        # Check for active legal holds
        active_holds = self.db.query(LegalHold).filter(
            and_(
                LegalHold.status == LegalHoldStatus.ACTIVE.value,
                LegalHold.data_types.contains([data_type]),
            )
        ).all()
        
        # Create purge record
        purge = DataPurgeRecord(
            purge_id=f"purge_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{policy_id}",
            policy_id=policy_id,
            purge_type="automated" if policy.auto_purge_enabled else "manual",
            data_type=data_type,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            organization_id=organization_id,
            started_at=datetime.utcnow(),
            executed_by=executed_by,
        )
        
        self.db.add(purge)
        self.db.commit()
        
        try:
            # Execute purge (this would call actual purge logic)
            records_purged, records_skipped = self._perform_purge(
                data_type=data_type,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                organization_id=organization_id,
                legal_holds=active_holds,
            )
            
            purge.records_purged = records_purged
            purge.records_skipped = records_skipped
            purge.purge_successful = True
            purge.completed_at = datetime.utcnow()
            purge.duration_seconds = int(
                (purge.completed_at - purge.started_at).total_seconds()
            )
        
        except Exception as e:
            logger.error(f"Purge execution failed: {e}", exc_info=True)
            purge.purge_successful = False
            purge.error_message = str(e)
            purge.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(purge)
        
        logger.info(
            f"Data purge executed: {purge.purge_id}",
            extra={
                "purge_id": purge.purge_id,
                "policy_id": policy_id,
                "records_purged": purge.records_purged,
                "records_skipped": purge.records_skipped,
                "event_type": "data_purge.executed",
            }
        )
        
        return purge
    
    def get_active_legal_holds(
        self,
        data_type: Optional[str] = None,
        organization_id: Optional[int] = None,
    ) -> List[LegalHold]:
        """
        Get active legal holds.
        
        Args:
            data_type: Filter by data type
            organization_id: Filter by organization
            
        Returns:
            List of active LegalHold records
        """
        query = self.db.query(LegalHold).filter(
            LegalHold.status == LegalHoldStatus.ACTIVE.value
        )
        
        if data_type:
            query = query.filter(LegalHold.data_types.contains([data_type]))
        
        if organization_id:
            query = query.filter(LegalHold.organization_id == organization_id)
        
        return query.all()
    
    def _perform_purge(
        self,
        data_type: str,
        date_range_start: datetime,
        date_range_end: datetime,
        organization_id: Optional[int],
        legal_holds: List[LegalHold],
    ) -> tuple[int, int]:
        """
        Perform actual data purge (placeholder - would integrate with actual data deletion).
        
        Args:
            data_type: Type of data
            date_range_start: Start date
            date_range_end: End date
            organization_id: Organization ID
            legal_holds: Active legal holds
            
        Returns:
            Tuple of (records_purged, records_skipped)
        """
        # This is a placeholder - in production, this would:
        # 1. Query the appropriate table based on data_type
        # 2. Filter by date range and organization
        # 3. Check against legal holds
        # 4. Delete records that are not under legal hold
        # 5. Return counts
        
        records_purged = 0
        records_skipped = len(legal_holds)  # Skip records under legal hold
        
        logger.info(
            f"Purge performed for {data_type}",
            extra={
                "data_type": data_type,
                "date_range_start": date_range_start.isoformat(),
                "date_range_end": date_range_end.isoformat(),
                "legal_holds_count": len(legal_holds),
            }
        )
        
        return records_purged, records_skipped
