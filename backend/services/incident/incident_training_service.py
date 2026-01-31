"""
IR-2: Incident Response Training Service for FedRAMP Compliance

Provides comprehensive incident response training management:
- Training curriculum management
- Role-specific training assignments
- Training completion tracking
- Tabletop exercise management
- Training compliance reporting
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from core.logger import logger
from models.incident import (
    IncidentTrainingCurriculum,
    IncidentTrainingRecord,
    TabletopExercise,
    TrainingRole,
    TrainingStatus,
)
from models.user import User
from utils.audit import record_audit


class IncidentTrainingService:
    """Service for managing incident response training per FedRAMP IR-2 requirements"""

    @staticmethod
    def create_curriculum(
        db: Session,
        org_id: int,
        name: str,
        target_role: TrainingRole,
        modules: List[Dict[str, Any]],
        duration_hours: int = 0,
        required_score_percent: int = 80,
        valid_for_days: int = 365,
        renewal_required: bool = True,
        description: Optional[str] = None,
        version: str = "1.0",
        created_by_user_id: Optional[int] = None,
        request=None,
    ) -> IncidentTrainingCurriculum:
        """Create a new training curriculum"""
        curriculum = IncidentTrainingCurriculum(
            org_id=org_id,
            name=name,
            description=description,
            target_role=target_role.value,
            modules=modules,
            duration_hours=duration_hours,
            required_score_percent=required_score_percent,
            valid_for_days=valid_for_days,
            renewal_required=renewal_required,
            version=version,
            created_by_user_id=created_by_user_id,
        )
        
        db.add(curriculum)
        db.commit()
        db.refresh(curriculum)
        
        # Audit log
        if request and created_by_user_id:
            try:
                user = db.query(User).filter(User.id == created_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="training_curriculum_created",
                        resource="incident_training_curriculum",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR2_CURRICULUM_CREATED",
                        after_state={
                            "curriculum_id": str(curriculum.id),
                            "name": name,
                            "target_role": target_role.value,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for curriculum creation: {e}", exc_info=True)
        
        logger.info(f"Training curriculum created: {name}, role={target_role.value}")
        return curriculum

    @staticmethod
    def assign_training(
        db: Session,
        org_id: int,
        user_id: int,
        curriculum_id: UUID,
        request=None,
    ) -> IncidentTrainingRecord:
        """Assign training curriculum to a user"""
        # Check if active record already exists
        existing = (
            db.query(IncidentTrainingRecord)
            .filter(
                IncidentTrainingRecord.org_id == org_id,
                IncidentTrainingRecord.user_id == user_id,
                IncidentTrainingRecord.curriculum_id == curriculum_id,
                IncidentTrainingRecord.status.in_([
                    TrainingStatus.NOT_STARTED.value,
                    TrainingStatus.IN_PROGRESS.value,
                ]),
            )
            .first()
        )
        
        if existing:
            return existing
        
        curriculum = db.query(IncidentTrainingCurriculum).filter(
            IncidentTrainingCurriculum.id == curriculum_id,
            IncidentTrainingCurriculum.org_id == org_id,
        ).first()
        
        if not curriculum:
            raise ValueError(f"Curriculum not found: {curriculum_id}")
        
        # Calculate expiration date
        expires_at = None
        if curriculum.valid_for_days > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(days=curriculum.valid_for_days)
        
        record = IncidentTrainingRecord(
            org_id=org_id,
            user_id=user_id,
            curriculum_id=curriculum_id,
            status=TrainingStatus.NOT_STARTED.value,
            expires_at=expires_at,
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="training_assigned",
                        resource="incident_training_record",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR2_TRAINING_ASSIGNED",
                        after_state={
                            "record_id": str(record.id),
                            "curriculum_id": str(curriculum_id),
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for training assignment: {e}", exc_info=True)
        
        logger.info(f"Training assigned: user_id={user_id}, curriculum_id={curriculum_id}")
        return record

    @staticmethod
    def start_training(
        db: Session,
        record_id: UUID,
        user_id: int,
        request=None,
    ) -> IncidentTrainingRecord:
        """Mark training as started"""
        record = db.query(IncidentTrainingRecord).filter(
            IncidentTrainingRecord.id == record_id,
            IncidentTrainingRecord.user_id == user_id,
        ).first()
        
        if not record:
            raise ValueError(f"Training record not found: {record_id}")
        
        if record.status == TrainingStatus.NOT_STARTED.value:
            record.status = TrainingStatus.IN_PROGRESS.value
            record.started_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(record)
        
        return record

    @staticmethod
    def complete_training(
        db: Session,
        record_id: UUID,
        user_id: int,
        score_percent: int,
        completed_modules: List[str],
        module_scores: Dict[str, int],
        request=None,
    ) -> IncidentTrainingRecord:
        """Mark training as completed with assessment results"""
        record = db.query(IncidentTrainingRecord).filter(
            IncidentTrainingRecord.id == record_id,
            IncidentTrainingRecord.user_id == user_id,
        ).first()
        
        if not record:
            raise ValueError(f"Training record not found: {record_id}")
        
        curriculum = db.query(IncidentTrainingCurriculum).filter(
            IncidentTrainingCurriculum.id == record.curriculum_id,
        ).first()
        
        passed = score_percent >= curriculum.required_score_percent
        
        record.status = TrainingStatus.COMPLETED.value if passed else TrainingStatus.IN_PROGRESS.value
        record.completed_at = datetime.now(timezone.utc)
        record.score_percent = score_percent
        record.passed = passed
        record.attempts = (record.attempts or 0) + 1
        record.completed_modules = completed_modules
        record.module_scores = module_scores
        
        # Update expiration if renewal required
        if passed and curriculum.renewal_required and curriculum.valid_for_days > 0:
            record.expires_at = datetime.now(timezone.utc) + timedelta(days=curriculum.valid_for_days)
        
        db.commit()
        db.refresh(record)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="training_completed",
                        resource="incident_training_record",
                        outcome="Success" if passed else "Failed",
                        classification="NON_PHI",
                        reason_code="IR2_TRAINING_COMPLETED",
                        after_state={
                            "record_id": str(record.id),
                            "score_percent": score_percent,
                            "passed": passed,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for training completion: {e}", exc_info=True)
        
        logger.info(
            f"Training completed: record_id={record_id}, "
            f"score={score_percent}%, passed={passed}"
        )
        return record

    @staticmethod
    def get_user_training_status(
        db: Session,
        org_id: int,
        user_id: int,
        role: Optional[TrainingRole] = None,
    ) -> List[Dict[str, Any]]:
        """Get training status for a user"""
        query = (
            db.query(IncidentTrainingRecord, IncidentTrainingCurriculum)
            .join(
                IncidentTrainingCurriculum,
                IncidentTrainingRecord.curriculum_id == IncidentTrainingCurriculum.id,
            )
            .filter(
                IncidentTrainingRecord.org_id == org_id,
                IncidentTrainingRecord.user_id == user_id,
            )
        )
        
        if role:
            query = query.filter(IncidentTrainingCurriculum.target_role == role.value)
        
        results = query.all()
        
        status_list = []
        for record, curriculum in results:
            is_expired = False
            if record.expires_at and record.expires_at < datetime.now(timezone.utc):
                is_expired = True
                if record.status == TrainingStatus.COMPLETED.value:
                    record.status = TrainingStatus.EXPIRED.value
                    db.commit()
            
            status_list.append({
                "record_id": str(record.id),
                "curriculum_id": str(curriculum.id),
                "curriculum_name": curriculum.name,
                "target_role": curriculum.target_role,
                "status": record.status,
                "is_expired": is_expired,
                "score_percent": record.score_percent,
                "passed": record.passed,
                "started_at": record.started_at.isoformat() if record.started_at else None,
                "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            })
        
        return status_list

    @staticmethod
    def create_tabletop_exercise(
        db: Session,
        org_id: int,
        name: str,
        scenario: str,
        exercise_date: datetime,
        participant_user_ids: List[int],
        facilitator_user_id: Optional[int] = None,
        description: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        created_by_user_id: Optional[int] = None,
        request=None,
    ) -> TabletopExercise:
        """Create a tabletop exercise"""
        exercise = TabletopExercise(
            org_id=org_id,
            name=name,
            description=description,
            scenario=scenario,
            exercise_date=exercise_date,
            duration_minutes=duration_minutes,
            participant_user_ids=participant_user_ids,
            facilitator_user_id=facilitator_user_id,
            created_by_user_id=created_by_user_id,
        )
        
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        
        # Audit log
        if request and created_by_user_id:
            try:
                user = db.query(User).filter(User.id == created_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="tabletop_exercise_created",
                        resource="tabletop_exercise",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR2_EXERCISE_CREATED",
                        after_state={
                            "exercise_id": str(exercise.id),
                            "name": name,
                            "participant_count": len(participant_user_ids),
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for exercise creation: {e}", exc_info=True)
        
        logger.info(f"Tabletop exercise created: {name}, participants={len(participant_user_ids)}")
        return exercise

    @staticmethod
    def complete_tabletop_exercise(
        db: Session,
        exercise_id: UUID,
        outcomes: str,
        strengths_identified: Optional[str] = None,
        areas_for_improvement: Optional[str] = None,
        participant_feedback: Optional[Dict[int, str]] = None,
        overall_rating: Optional[int] = None,
        request=None,
    ) -> TabletopExercise:
        """Complete a tabletop exercise with results"""
        exercise = db.query(TabletopExercise).filter(
            TabletopExercise.id == exercise_id,
        ).first()
        
        if not exercise:
            raise ValueError(f"Exercise not found: {exercise_id}")
        
        exercise.status = "completed"
        exercise.outcomes = outcomes
        exercise.strengths_identified = strengths_identified
        exercise.areas_for_improvement = areas_for_improvement
        exercise.participant_feedback = participant_feedback
        exercise.overall_rating = overall_rating
        
        db.commit()
        db.refresh(exercise)
        
        logger.info(f"Tabletop exercise completed: {exercise.name}")
        return exercise

    @staticmethod
    def get_training_compliance_report(
        db: Session,
        org_id: int,
        role: Optional[TrainingRole] = None,
    ) -> Dict[str, Any]:
        """Generate training compliance report"""
        # Get all curricula for role
        curricula_query = db.query(IncidentTrainingCurriculum).filter(
            IncidentTrainingCurriculum.org_id == org_id,
            IncidentTrainingCurriculum.is_active == True,
        )
        
        if role:
            curricula_query = curricula_query.filter(
                IncidentTrainingCurriculum.target_role == role.value,
            )
        
        curricula = curricula_query.all()
        
        # Get all users in org
        users = db.query(User).filter(User.org_id == org_id).all()
        
        compliance_data = {
            "total_curricula": len(curricula),
            "total_users": len(users),
            "curricula": [],
        }
        
        for curriculum in curricula:
            # Get training records for this curriculum
            records = (
                db.query(IncidentTrainingRecord)
                .filter(
                    IncidentTrainingRecord.org_id == org_id,
                    IncidentTrainingRecord.curriculum_id == curriculum.id,
                )
                .all()
            )
            
            now = datetime.now(timezone.utc)
            completed = [r for r in records if r.status == TrainingStatus.COMPLETED.value]
            expired = [
                r for r in completed
                if r.expires_at and r.expires_at < now
            ]
            in_progress = [r for r in records if r.status == TrainingStatus.IN_PROGRESS.value]
            not_started = [r for r in records if r.status == TrainingStatus.NOT_STARTED.value]
            
            compliance_data["curricula"].append({
                "curriculum_id": str(curriculum.id),
                "name": curriculum.name,
                "target_role": curriculum.target_role,
                "total_assigned": len(records),
                "completed": len(completed),
                "expired": len(expired),
                "in_progress": len(in_progress),
                "not_started": len(not_started),
                "compliance_percent": (
                    (len(completed) - len(expired)) / len(users) * 100
                    if len(users) > 0 else 0
                ),
            })
        
        return compliance_data
