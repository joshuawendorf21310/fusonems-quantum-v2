"""
FedRAMP Compliance Dashboard Router
Provides compliance status and ConMon reporting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from core.database import get_db
from core.security import require_roles
from models.user import User, UserRole
from services.compliance.fedramp_dashboard import FedRAMPDashboardService
from services.compliance.continuous_monitoring import ContinuousMonitoringService
from services.compliance.time_sync_service import time_sync_service
from utils.fips_validator import validate_fips_compliance


router = APIRouter(prefix="/api/compliance/fedramp", tags=["FedRAMP Compliance"])


class ConMonReportRequest(BaseModel):
    start_date: str  # ISO format
    end_date: str    # ISO format
    org_id: int | None = None


@router.get("/dashboard")
def get_fedramp_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """
    FedRAMP Compliance Dashboard
    
    Returns comprehensive compliance status across all control families
    """
    dashboard = FedRAMPDashboardService(db)
    return dashboard.get_comprehensive_status()


@router.get("/conmon/monthly-report")
def get_conmon_monthly_report(
    month_offset: int = 0,  # 0 = current month, 1 = last month, etc.
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """
    FedRAMP Continuous Monitoring Monthly Report
    
    Required monthly for active FedRAMP authorizations
    """
    conmon = ContinuousMonitoringService(db)
    
    # Calculate month boundaries
    now = datetime.now(timezone.utc)
    if month_offset == 0:
        # Current month to date
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    else:
        # Previous month
        end_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    return conmon.generate_conmon_report(start_date, end_date)


@router.post("/conmon/generate-report")
def generate_custom_conmon_report(
    request: ConMonReportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Generate custom ConMon report for specific date range"""
    conmon = ContinuousMonitoringService(db)
    
    try:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {e}"
        )
    
    return conmon.generate_conmon_report(start_date, end_date, request.org_id)


@router.get("/time-sync/status")
def check_time_sync_status(
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """
    Check time synchronization status (AU-8)
    FedRAMP requires ±5 seconds of authoritative time source
    """
    return time_sync_service.check_time_drift()


@router.get("/fips/status")
def check_fips_status(
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """
    Check FIPS 140-2 compliance status (SC-13)
    """
    try:
        return validate_fips_compliance()
    except Exception as e:
        return {
            "compliant": False,
            "error": str(e),
            "message": "FIPS validation check failed"
        }


@router.get("/compliance-posture")
def get_compliance_posture(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """
    Overall compliance posture assessment
    """
    conmon = ContinuousMonitoringService(db)
    return conmon.check_compliance_posture()


@router.get("/readiness-assessment")
def assess_readiness(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder))
):
    """
    Assess readiness for FedRAMP authorization
    
    Returns assessment of technical readiness, documentation status,
    and recommendations for next steps
    """
    dashboard = FedRAMPDashboardService(db)
    status = dashboard.get_comprehensive_status()
    
    return {
        "overall_compliance": status["overall_compliance"],
        "technical_readiness": status["technical_readiness"],
        "security_posture": status["security_posture"],
        "control_families": status["control_families"],
        "next_steps": status["recommendations"],
        "estimated_effort": {
            "remaining_controls": 421 - status["overall_compliance"]["total_controls_implemented"],
            "estimated_months": 10,
            "3pao_assessment_months": 2,
            "authorization_months": 2
        }
    }
