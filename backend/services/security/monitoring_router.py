"""
Security Monitoring Router for FedRAMP SI-4 Compliance

Provides API endpoints for:
- Security dashboard
- Real-time metrics
- Alert management
- Threat feed
- Security event queries

FedRAMP SI-4: Information System Monitoring requires accessible
monitoring capabilities for security operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_user
from core.security import require_roles
from models.user import User, UserRole
from models.security_event import (
    SecurityEvent,
    SecurityAlert,
    EventSeverity,
    SecurityEventType,
    AlertStatus,
    InvestigationStatus,
)
from services.security.security_monitoring_service import SecurityMonitoringService
from utils.logger import logger


router = APIRouter(
    prefix="/api/v1/security/monitoring",
    tags=["Security Monitoring"],
)


# ============================================================================
# Request/Response Models
# ============================================================================


class SecurityMetricsResponse(BaseModel):
    """Security metrics response"""
    total_events_24h: int
    total_events_7d: int
    total_events_30d: int
    events_by_severity: dict[str, int]
    events_by_type: dict[str, int]
    active_alerts: int
    alerts_by_status: dict[str, int]
    anomalies_detected_24h: int
    threat_intelligence_matches_24h: int
    avg_response_time_seconds: float
    investigation_backlog: int


class SecurityEventResponse(BaseModel):
    """Security event response"""
    id: UUID
    timestamp: datetime
    event_type: str
    severity: str
    title: str
    description: str
    source: str
    ip_address: Optional[str] = None
    user_email: Optional[str] = None
    alert_generated: bool
    alert_status: Optional[str] = None
    threat_intelligence_matched: bool
    behavioral_anomaly_detected: bool
    behavioral_risk_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class SecurityAlertResponse(BaseModel):
    """Security alert response"""
    id: UUID
    event_id: UUID
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[int] = None
    
    class Config:
        from_attributes = True


class SecurityEventListResponse(BaseModel):
    """Security event list response"""
    events: List[SecurityEventResponse]
    total: int
    limit: int
    offset: int


class SecurityAlertListResponse(BaseModel):
    """Security alert list response"""
    alerts: List[SecurityAlertResponse]
    total: int
    limit: int
    offset: int


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert"""
    notes: Optional[str] = None


class UpdateInvestigationRequest(BaseModel):
    """Request to update investigation status"""
    investigation_status: InvestigationStatus
    investigation_notes: Optional[str] = None
    assigned_to: Optional[int] = None


# ============================================================================
# Dashboard Endpoints
# ============================================================================


@router.get("/dashboard/metrics", response_model=SecurityMetricsResponse)
def get_security_metrics(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
):
    """
    Get security metrics for dashboard.
    
    Returns real-time security metrics including:
    - Event counts and trends
    - Alert statistics
    - Anomaly detection metrics
    - Threat intelligence matches
    - Investigation backlog
    """
    monitoring_service = SecurityMonitoringService(db)
    metrics = monitoring_service.get_security_metrics(
        org_id=user.org_id,
        time_window_hours=24
    )
    
    return SecurityMetricsResponse(
        total_events_24h=metrics.total_events_24h,
        total_events_7d=metrics.total_events_7d,
        total_events_30d=metrics.total_events_30d,
        events_by_severity=metrics.events_by_severity,
        events_by_type=metrics.events_by_type,
        active_alerts=metrics.active_alerts,
        alerts_by_status=metrics.alerts_by_status,
        anomalies_detected_24h=metrics.anomalies_detected_24h,
        threat_intelligence_matches_24h=metrics.threat_intelligence_matches_24h,
        avg_response_time_seconds=metrics.avg_response_time_seconds,
        investigation_backlog=metrics.investigation_backlog,
    )


@router.get("/dashboard/realtime", response_model=SecurityMetricsResponse)
def get_realtime_metrics(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
    time_window_minutes: int = Query(5, ge=1, le=60),
):
    """
    Get real-time security metrics.
    
    Returns metrics for a short time window (default 5 minutes)
    for real-time monitoring dashboards.
    """
    monitoring_service = SecurityMonitoringService(db)
    metrics = monitoring_service.get_security_metrics(
        org_id=user.org_id,
        time_window_hours=time_window_minutes / 60.0
    )
    
    return SecurityMetricsResponse(
        total_events_24h=metrics.total_events_24h,
        total_events_7d=metrics.total_events_7d,
        total_events_30d=metrics.total_events_30d,
        events_by_severity=metrics.events_by_severity,
        events_by_type=metrics.events_by_type,
        active_alerts=metrics.active_alerts,
        alerts_by_status=metrics.alerts_by_status,
        anomalies_detected_24h=metrics.anomalies_detected_24h,
        threat_intelligence_matches_24h=metrics.threat_intelligence_matches_24h,
        avg_response_time_seconds=metrics.avg_response_time_seconds,
        investigation_backlog=metrics.investigation_backlog,
    )


# ============================================================================
# Security Events Endpoints
# ============================================================================


@router.get("/events", response_model=SecurityEventListResponse)
def list_security_events(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
    severity: Optional[EventSeverity] = Query(None),
    event_type: Optional[SecurityEventType] = Query(None),
    alert_status: Optional[AlertStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    List security events with filters.
    
    Returns paginated list of security events filtered by:
    - Severity level
    - Event type
    - Alert status
    """
    monitoring_service = SecurityMonitoringService(db)
    
    severity_str = severity.value if severity else None
    event_type_str = event_type.value if event_type else None
    alert_status_str = alert_status.value if alert_status else None
    
    events, total = monitoring_service.list_security_events(
        org_id=user.org_id,
        severity=severity_str,
        event_type=event_type_str,
        alert_status=alert_status_str,
        limit=limit,
        offset=offset,
    )
    
    return SecurityEventListResponse(
        events=[SecurityEventResponse.from_orm(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/events/{event_id}", response_model=SecurityEventResponse)
def get_security_event(
    event_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
):
    """
    Get security event by ID.
    
    Returns detailed information about a specific security event.
    """
    event = db.query(SecurityEvent).filter(
        SecurityEvent.id == event_id,
        SecurityEvent.org_id == user.org_id,
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security event not found"
        )
    
    return SecurityEventResponse.from_orm(event)


# ============================================================================
# Alert Management Endpoints
# ============================================================================


@router.get("/alerts", response_model=SecurityAlertListResponse)
def list_security_alerts(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
    status: Optional[AlertStatus] = Query(None),
    severity: Optional[EventSeverity] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    List security alerts with filters.
    
    Returns paginated list of security alerts filtered by:
    - Alert status
    - Severity level
    """
    query = db.query(SecurityAlert).filter(
        SecurityAlert.org_id == user.org_id,
        SecurityAlert.training_mode == False,
    )
    
    if status:
        query = query.filter(SecurityAlert.status == status.value)
    
    if severity:
        query = query.filter(SecurityAlert.severity == severity.value)
    
    total = query.count()
    alerts = query.order_by(
        SecurityAlert.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return SecurityAlertListResponse(
        alerts=[SecurityAlertResponse.from_orm(a) for a in alerts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/alerts/{alert_id}", response_model=SecurityAlertResponse)
def get_security_alert(
    alert_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
):
    """
    Get security alert by ID.
    
    Returns detailed information about a specific security alert.
    """
    alert = db.query(SecurityAlert).filter(
        SecurityAlert.id == alert_id,
        SecurityAlert.org_id == user.org_id,
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security alert not found"
        )
    
    return SecurityAlertResponse.from_orm(alert)


@router.post("/alerts/{alert_id}/acknowledge", response_model=SecurityAlertResponse)
def acknowledge_alert(
    alert_id: UUID,
    request: AcknowledgeAlertRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
):
    """
    Acknowledge a security alert.
    
    Marks an alert as acknowledged and records who acknowledged it.
    """
    monitoring_service = SecurityMonitoringService(db)
    alert = monitoring_service.acknowledge_alert(
        alert_id=str(alert_id),
        user_id=user.id
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security alert not found"
        )
    
    if alert.org_id != user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    logger.info(
        f"Alert acknowledged: alert_id={alert_id}, user_id={user.id}",
        extra={
            "alert_id": str(alert_id),
            "user_id": user.id,
            "event_type": "security.monitoring.alert_acknowledged",
        }
    )
    
    return SecurityAlertResponse.from_orm(alert)


@router.post("/alerts/{alert_id}/resolve", response_model=SecurityAlertResponse)
def resolve_alert(
    alert_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
):
    """
    Resolve a security alert.
    
    Marks an alert as resolved.
    """
    alert = db.query(SecurityAlert).filter(
        SecurityAlert.id == alert_id,
        SecurityAlert.org_id == user.org_id,
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security alert not found"
        )
    
    alert.status = AlertStatus.RESOLVED.value
    alert.resolved_at = datetime.utcnow()
    
    # Update related security event
    if alert.event_id:
        event = db.query(SecurityEvent).filter(
            SecurityEvent.id == alert.event_id
        ).first()
        if event:
            event.alert_status = AlertStatus.RESOLVED.value
    
    db.commit()
    db.refresh(alert)
    
    logger.info(
        f"Alert resolved: alert_id={alert_id}, user_id={user.id}",
        extra={
            "alert_id": str(alert_id),
            "user_id": user.id,
            "event_type": "security.monitoring.alert_resolved",
        }
    )
    
    return SecurityAlertResponse.from_orm(alert)


# ============================================================================
# Investigation Management Endpoints
# ============================================================================


@router.post("/events/{event_id}/investigation", response_model=SecurityEventResponse)
def update_investigation(
    event_id: UUID,
    request: UpdateInvestigationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
):
    """
    Update investigation status for a security event.
    
    Updates the investigation status, notes, and assignment.
    """
    event = db.query(SecurityEvent).filter(
        SecurityEvent.id == event_id,
        SecurityEvent.org_id == user.org_id,
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security event not found"
        )
    
    event.investigation_status = request.investigation_status.value
    
    if request.investigation_notes:
        if event.investigation_notes:
            event.investigation_notes += f"\n\n[{datetime.utcnow().isoformat()}] {request.investigation_notes}"
        else:
            event.investigation_notes = request.investigation_notes
    
    if request.assigned_to:
        event.investigation_assigned_to = request.assigned_to
    
    if request.investigation_status == InvestigationStatus.IN_PROGRESS:
        if not event.investigation_started_at:
            event.investigation_started_at = datetime.utcnow()
    elif request.investigation_status == InvestigationStatus.COMPLETED:
        event.investigation_completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(event)
    
    logger.info(
        f"Investigation updated: event_id={event_id}, status={request.investigation_status.value}, user_id={user.id}",
        extra={
            "event_id": str(event_id),
            "investigation_status": request.investigation_status.value,
            "user_id": user.id,
            "event_type": "security.monitoring.investigation_updated",
        }
    )
    
    return SecurityEventResponse.from_orm(event)


# ============================================================================
# Threat Intelligence Endpoints
# ============================================================================


@router.get("/threat-feed")
def get_threat_feed(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.compliance)),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get threat intelligence feed.
    
    Returns security events that matched threat intelligence indicators.
    """
    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
    
    events = db.query(SecurityEvent).filter(
        SecurityEvent.org_id == user.org_id,
        SecurityEvent.threat_intelligence_matched == True,
        SecurityEvent.timestamp >= cutoff_24h,
        SecurityEvent.training_mode == False,
    ).order_by(
        SecurityEvent.timestamp.desc()
    ).offset(offset).limit(limit).all()
    
    total = db.query(SecurityEvent).filter(
        SecurityEvent.org_id == user.org_id,
        SecurityEvent.threat_intelligence_matched == True,
        SecurityEvent.timestamp >= cutoff_24h,
        SecurityEvent.training_mode == False,
    ).count()
    
    return {
        "events": [SecurityEventResponse.from_orm(e) for e in events],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
