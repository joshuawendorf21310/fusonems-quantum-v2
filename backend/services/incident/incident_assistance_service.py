"""
IR-7: Incident Response Assistance Service for FedRAMP Compliance

Provides comprehensive incident response assistance capabilities:
- Help desk integration
- Expert contact management
- Resource availability tracking
- Assistance request tracking
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from core.logger import logger
from models.incident import (
    IncidentAssistanceRequest,
    IncidentExpertContact,
    AssistanceRequestStatus,
)
from models.user import User
from utils.audit import record_audit


class IncidentAssistanceService:
    """Service for managing incident response assistance per FedRAMP IR-7 requirements"""

    @staticmethod
    def create_assistance_request(
        db: Session,
        org_id: int,
        requested_by_user_id: int,
        request_type: str,
        description: str,
        priority: str = "normal",
        incident_id: Optional[UUID] = None,
        request=None,
    ) -> IncidentAssistanceRequest:
        """Create a new assistance request"""
        assistance_request = IncidentAssistanceRequest(
            org_id=org_id,
            incident_id=incident_id,
            requested_by_user_id=requested_by_user_id,
            request_type=request_type,
            description=description,
            priority=priority,
            status=AssistanceRequestStatus.OPEN.value,
        )
        
        db.add(assistance_request)
        db.commit()
        db.refresh(assistance_request)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == requested_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="assistance_request_created",
                        resource="incident_assistance_request",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR7_ASSISTANCE_REQUESTED",
                        after_state={
                            "request_id": str(assistance_request.id),
                            "request_type": request_type,
                            "priority": priority,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for assistance request: {e}", exc_info=True)
        
        logger.info(
            f"Assistance request created: type={request_type}, "
            f"priority={priority}, requested_by={requested_by_user_id}"
        )
        return assistance_request

    @staticmethod
    def assign_assistance_request(
        db: Session,
        request_id: UUID,
        assigned_to_user_id: int,
        assigned_by_user_id: int,
        request=None,
    ) -> IncidentAssistanceRequest:
        """Assign an assistance request to a responder"""
        assistance_request = db.query(IncidentAssistanceRequest).filter(
            IncidentAssistanceRequest.id == request_id,
        ).first()
        
        if not assistance_request:
            raise ValueError(f"Assistance request not found: {request_id}")
        
        assistance_request.assigned_to_user_id = assigned_to_user_id
        assistance_request.assigned_at = datetime.now(timezone.utc)
        assistance_request.status = AssistanceRequestStatus.IN_PROGRESS.value
        
        db.commit()
        db.refresh(assistance_request)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == assigned_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="assistance_request_assigned",
                        resource="incident_assistance_request",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR7_ASSISTANCE_ASSIGNED",
                        after_state={
                            "request_id": str(request_id),
                            "assigned_to_user_id": assigned_to_user_id,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for assignment: {e}", exc_info=True)
        
        logger.info(f"Assistance request assigned: request_id={request_id}, assigned_to={assigned_to_user_id}")
        return assistance_request

    @staticmethod
    def resolve_assistance_request(
        db: Session,
        request_id: UUID,
        resolved_by_user_id: int,
        resolution_notes: str,
        request=None,
    ) -> IncidentAssistanceRequest:
        """Resolve an assistance request"""
        assistance_request = db.query(IncidentAssistanceRequest).filter(
            IncidentAssistanceRequest.id == request_id,
        ).first()
        
        if not assistance_request:
            raise ValueError(f"Assistance request not found: {request_id}")
        
        now = datetime.now(timezone.utc)
        assistance_request.status = AssistanceRequestStatus.RESOLVED.value
        assistance_request.resolved_at = now
        assistance_request.resolution_notes = resolution_notes
        
        # Calculate resolution time
        if assistance_request.created_at:
            resolution_time = (now - assistance_request.created_at).total_seconds() / 60
            assistance_request.resolution_time_minutes = int(resolution_time)
        
        db.commit()
        db.refresh(assistance_request)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == resolved_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="assistance_request_resolved",
                        resource="incident_assistance_request",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR7_ASSISTANCE_RESOLVED",
                        after_state={
                            "request_id": str(request_id),
                            "resolution_time_minutes": assistance_request.resolution_time_minutes,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for resolution: {e}", exc_info=True)
        
        logger.info(f"Assistance request resolved: request_id={request_id}")
        return assistance_request

    @staticmethod
    def add_expert_contact(
        db: Session,
        org_id: int,
        name: str,
        email: str,
        expertise_areas: List[str],
        phone: Optional[str] = None,
        organization: Optional[str] = None,
        title: Optional[str] = None,
        specializations: Optional[str] = None,
        preferred_contact_method: Optional[str] = None,
        is_available: bool = True,
        availability_notes: Optional[str] = None,
        created_by_user_id: Optional[int] = None,
        request=None,
    ) -> IncidentExpertContact:
        """Add an expert contact to the directory"""
        expert = IncidentExpertContact(
            org_id=org_id,
            name=name,
            email=email,
            phone=phone,
            organization=organization,
            title=title,
            expertise_areas=expertise_areas,
            specializations=specializations,
            preferred_contact_method=preferred_contact_method,
            is_available=is_available,
            availability_notes=availability_notes,
            created_by_user_id=created_by_user_id,
        )
        
        db.add(expert)
        db.commit()
        db.refresh(expert)
        
        # Audit log
        if request and created_by_user_id:
            try:
                user = db.query(User).filter(User.id == created_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="expert_contact_added",
                        resource="incident_expert_contact",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR7_EXPERT_ADDED",
                        after_state={
                            "expert_id": str(expert.id),
                            "name": name,
                            "expertise_areas": expertise_areas,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for expert addition: {e}", exc_info=True)
        
        logger.info(f"Expert contact added: {name}, expertise={expertise_areas}")
        return expert

    @staticmethod
    def find_experts(
        db: Session,
        org_id: int,
        expertise_area: Optional[str] = None,
        available_only: bool = True,
    ) -> List[IncidentExpertContact]:
        """Find experts by expertise area"""
        query = db.query(IncidentExpertContact).filter(
            IncidentExpertContact.org_id == org_id,
        )
        
        if available_only:
            query = query.filter(IncidentExpertContact.is_available == True)
        
        if expertise_area:
            # Filter by expertise area (JSON array contains)
            query = query.filter(
                IncidentExpertContact.expertise_areas.contains([expertise_area])
            )
        
        return query.all()

    @staticmethod
    def update_expert_availability(
        db: Session,
        expert_id: UUID,
        is_available: bool,
        availability_notes: Optional[str] = None,
        request=None,
    ) -> IncidentExpertContact:
        """Update expert availability status"""
        expert = db.query(IncidentExpertContact).filter(
            IncidentExpertContact.id == expert_id,
        ).first()
        
        if not expert:
            raise ValueError(f"Expert contact not found: {expert_id}")
        
        expert.is_available = is_available
        if availability_notes is not None:
            expert.availability_notes = availability_notes
        
        db.commit()
        db.refresh(expert)
        
        logger.info(f"Expert availability updated: expert_id={expert_id}, available={is_available}")
        return expert

    @staticmethod
    def get_assistance_requests(
        db: Session,
        org_id: int,
        status: Optional[AssistanceRequestStatus] = None,
        incident_id: Optional[UUID] = None,
        assigned_to_user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[IncidentAssistanceRequest]:
        """Get assistance requests with filters"""
        query = db.query(IncidentAssistanceRequest).filter(
            IncidentAssistanceRequest.org_id == org_id,
        )
        
        if status:
            query = query.filter(IncidentAssistanceRequest.status == status.value)
        
        if incident_id:
            query = query.filter(IncidentAssistanceRequest.incident_id == incident_id)
        
        if assigned_to_user_id:
            query = query.filter(IncidentAssistanceRequest.assigned_to_user_id == assigned_to_user_id)
        
        return query.order_by(desc(IncidentAssistanceRequest.created_at)).limit(limit).offset(offset).all()

    @staticmethod
    def get_assistance_metrics(
        db: Session,
        org_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get assistance request metrics"""
        query = db.query(IncidentAssistanceRequest).filter(
            IncidentAssistanceRequest.org_id == org_id,
        )
        
        if start_date:
            query = query.filter(IncidentAssistanceRequest.created_at >= start_date)
        
        if end_date:
            query = query.filter(IncidentAssistanceRequest.created_at <= end_date)
        
        requests = query.all()
        
        total_requests = len(requests)
        open_requests = sum(1 for r in requests if r.status == AssistanceRequestStatus.OPEN.value)
        in_progress = sum(1 for r in requests if r.status == AssistanceRequestStatus.IN_PROGRESS.value)
        resolved = sum(1 for r in requests if r.status == AssistanceRequestStatus.RESOLVED.value)
        
        resolved_with_time = [r for r in requests if r.resolution_time_minutes]
        avg_resolution_time = (
            sum(r.resolution_time_minutes for r in resolved_with_time) / len(resolved_with_time)
            if resolved_with_time else None
        )
        
        # Group by request type
        by_type = {}
        for req in requests:
            by_type[req.request_type] = by_type.get(req.request_type, 0) + 1
        
        return {
            "total_requests": total_requests,
            "open_requests": open_requests,
            "in_progress_requests": in_progress,
            "resolved_requests": resolved,
            "average_resolution_time_minutes": avg_resolution_time,
            "requests_by_type": by_type,
        }
