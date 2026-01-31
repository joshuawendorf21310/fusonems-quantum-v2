"""
AT-4: Security Training Records Service
Implements FedRAMP AT-4 requirements for training history, compliance reporting, and certificate management.
"""
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.awareness_training import (
    SecurityTrainingRecord,
    TrainingStatus,
    TrainingDeliveryMethod,
    CompetencyLevel,
)
from models.user import User
from core.logger import logger


class TrainingRecordsService:
    """Service for managing security training records per FedRAMP AT-4"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_training_record(
        self,
        org_id: int,
        user_id: int,
        training_type: str,  # awareness, role_based, external, etc.
        training_name: str,
        training_provider: Optional[str] = None,
        training_code: Optional[str] = None,
        training_date: date = None,
        completion_date: Optional[date] = None,
        delivery_method: TrainingDeliveryMethod = TrainingDeliveryMethod.ONLINE,
        duration_hours: float = 1.0,
        status: TrainingStatus = TrainingStatus.COMPLETED,
        score_percentage: Optional[float] = None,
        passed: Optional[bool] = None,
        certificate_issued: bool = False,
        certificate_number: Optional[str] = None,
        certificate_issue_date: Optional[date] = None,
        certificate_expiration_date: Optional[date] = None,
        certificate_document_path: Optional[str] = None,
        competency_level_achieved: Optional[CompetencyLevel] = None,
        competency_validated: bool = False,
        competency_validated_by_user_id: Optional[int] = None,
        external_training: bool = False,
        external_provider_name: Optional[str] = None,
        external_training_id: Optional[str] = None,
        ceu_credits: float = 0.0,
        cme_credits: float = 0.0,
        compliance_required: bool = True,
        notes: Optional[str] = None,
        recorded_by_user_id: int = None,
    ) -> SecurityTrainingRecord:
        """
        Create a security training record.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            training_type: Type of training
            training_name: Training name
            training_provider: Training provider
            training_code: Training code
            training_date: Training date
            completion_date: Completion date
            delivery_method: Delivery method
            duration_hours: Duration in hours
            status: Training status
            score_percentage: Score percentage
            passed: Whether passed
            certificate_issued: Whether certificate was issued
            certificate_number: Certificate number
            certificate_issue_date: Certificate issue date
            certificate_expiration_date: Certificate expiration date
            certificate_document_path: Path to certificate document
            competency_level_achieved: Competency level achieved
            competency_validated: Whether competency was validated
            competency_validated_by_user_id: User who validated competency
            external_training: Whether external training
            external_provider_name: External provider name
            external_training_id: External training ID
            ceu_credits: CEU credits earned
            cme_credits: CME credits earned
            compliance_required: Whether compliance is required
            notes: Additional notes
            recorded_by_user_id: User recording the training
            
        Returns:
            Created SecurityTrainingRecord
        """
        try:
            training_date = training_date or date.today()
            
            # Determine compliance status
            compliance_status = None
            if compliance_required:
                if status == TrainingStatus.COMPLETED and (passed is None or passed):
                    compliance_status = "compliant"
                elif status == TrainingStatus.COMPLETED and passed == False:
                    compliance_status = "non_compliant"
                else:
                    compliance_status = "pending"
            
            record = SecurityTrainingRecord(
                org_id=org_id,
                user_id=user_id,
                training_type=training_type,
                training_name=training_name,
                training_provider=training_provider,
                training_code=training_code,
                training_date=training_date,
                completion_date=completion_date,
                delivery_method=delivery_method,
                duration_hours=duration_hours,
                status=status,
                score_percentage=score_percentage,
                passed=passed,
                certificate_issued=certificate_issued,
                certificate_number=certificate_number,
                certificate_issue_date=certificate_issue_date,
                certificate_expiration_date=certificate_expiration_date,
                certificate_document_path=certificate_document_path,
                competency_level_achieved=competency_level_achieved,
                competency_validated=competency_validated,
                competency_validated_by_user_id=competency_validated_by_user_id,
                external_training=external_training,
                external_provider_name=external_provider_name,
                external_training_id=external_training_id,
                ceu_credits=ceu_credits,
                cme_credits=cme_credits,
                compliance_required=compliance_required,
                compliance_status=compliance_status,
                notes=notes,
                recorded_by_user_id=recorded_by_user_id,
            )
            
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            
            logger.info(
                f"Created training record for user {user_id}",
                extra={
                    "org_id": org_id,
                    "user_id": user_id,
                    "training_name": training_name,
                    "event_type": "training_record.created",
                }
            )
            
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create training record: {e}", exc_info=True)
            raise
    
    def update_certificate(
        self,
        record_id: int,
        org_id: int,
        certificate_number: Optional[str] = None,
        certificate_issue_date: Optional[date] = None,
        certificate_expiration_date: Optional[date] = None,
        certificate_document_path: Optional[str] = None,
    ) -> SecurityTrainingRecord:
        """
        Update certificate information for a training record.
        
        Args:
            record_id: Record ID
            org_id: Organization ID (for verification)
            certificate_number: Certificate number
            certificate_issue_date: Certificate issue date
            certificate_expiration_date: Certificate expiration date
            certificate_document_path: Path to certificate document
            
        Returns:
            Updated SecurityTrainingRecord
        """
        try:
            record = self.db.query(SecurityTrainingRecord).filter(
                SecurityTrainingRecord.id == record_id,
                SecurityTrainingRecord.org_id == org_id,
            ).first()
            
            if not record:
                raise ValueError(f"Training record {record_id} not found")
            
            record.certificate_issued = True
            if certificate_number:
                record.certificate_number = certificate_number
            if certificate_issue_date:
                record.certificate_issue_date = certificate_issue_date
            if certificate_expiration_date:
                record.certificate_expiration_date = certificate_expiration_date
            if certificate_document_path:
                record.certificate_document_path = certificate_document_path
            
            record.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(record)
            
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update certificate: {e}", exc_info=True)
            raise
    
    def get_training_record(
        self,
        record_id: int,
        org_id: int,
    ) -> Optional[SecurityTrainingRecord]:
        """Get a training record by ID"""
        return self.db.query(SecurityTrainingRecord).filter(
            SecurityTrainingRecord.id == record_id,
            SecurityTrainingRecord.org_id == org_id,
        ).first()
    
    def list_training_records(
        self,
        org_id: int,
        user_id: Optional[int] = None,
        training_type: Optional[str] = None,
        status: Optional[TrainingStatus] = None,
        compliance_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SecurityTrainingRecord]:
        """
        List training records for an organization.
        
        Args:
            org_id: Organization ID
            user_id: Filter by user ID (optional)
            training_type: Filter by training type (optional)
            status: Filter by status (optional)
            compliance_status: Filter by compliance status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of SecurityTrainingRecord
        """
        query = self.db.query(SecurityTrainingRecord).filter(
            SecurityTrainingRecord.org_id == org_id,
        )
        
        if user_id:
            query = query.filter(SecurityTrainingRecord.user_id == user_id)
        
        if training_type:
            query = query.filter(SecurityTrainingRecord.training_type == training_type)
        
        if status:
            query = query.filter(SecurityTrainingRecord.status == status)
        
        if compliance_status:
            query = query.filter(SecurityTrainingRecord.compliance_status == compliance_status)
        
        return query.order_by(
            SecurityTrainingRecord.training_date.desc()
        ).limit(limit).offset(offset).all()
    
    def get_user_training_history(
        self,
        org_id: int,
        user_id: int,
        limit: int = 100,
    ) -> List[SecurityTrainingRecord]:
        """
        Get complete training history for a user.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            limit: Maximum number of results
            
        Returns:
            List of SecurityTrainingRecord
        """
        return self.db.query(SecurityTrainingRecord).filter(
            SecurityTrainingRecord.org_id == org_id,
            SecurityTrainingRecord.user_id == user_id,
        ).order_by(
            SecurityTrainingRecord.training_date.desc()
        ).limit(limit).all()
    
    def get_expiring_certificates(
        self,
        org_id: int,
        days_ahead: int = 90,
    ) -> List[SecurityTrainingRecord]:
        """
        Get training records with expiring certificates.
        
        Args:
            org_id: Organization ID
            days_ahead: Number of days ahead to check (default 90)
            
        Returns:
            List of SecurityTrainingRecord with expiring certificates
        """
        from datetime import timedelta
        today = date.today()
        threshold = today + timedelta(days=days_ahead)
        
        return self.db.query(SecurityTrainingRecord).filter(
            SecurityTrainingRecord.org_id == org_id,
            SecurityTrainingRecord.certificate_expiration_date <= threshold,
            SecurityTrainingRecord.certificate_expiration_date >= today,
            SecurityTrainingRecord.certificate_issued == True,
        ).order_by(SecurityTrainingRecord.certificate_expiration_date).all()
    
    def get_compliance_report(
        self,
        org_id: int,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get compliance report for training records.
        
        Args:
            org_id: Organization ID
            user_id: Filter by user ID (optional)
            
        Returns:
            Dictionary with compliance statistics
        """
        query = self.db.query(SecurityTrainingRecord).filter(
            SecurityTrainingRecord.org_id == org_id,
            SecurityTrainingRecord.compliance_required == True,
        )
        
        if user_id:
            query = query.filter(SecurityTrainingRecord.user_id == user_id)
        
        records = query.all()
        
        report = {
            "total_records": len(records),
            "compliant": 0,
            "non_compliant": 0,
            "pending": 0,
            "by_training_type": {},
        }
        
        for record in records:
            if record.compliance_status == "compliant":
                report["compliant"] += 1
            elif record.compliance_status == "non_compliant":
                report["non_compliant"] += 1
            else:
                report["pending"] += 1
            
            if record.training_type not in report["by_training_type"]:
                report["by_training_type"][record.training_type] = {
                    "total": 0,
                    "compliant": 0,
                    "non_compliant": 0,
                    "pending": 0,
                }
            
            report["by_training_type"][record.training_type]["total"] += 1
            if record.compliance_status:
                report["by_training_type"][record.training_type][record.compliance_status] += 1
        
        return report
