"""
SA-21: Developer Screening Service

FedRAMP SA-21 compliance service for:
- Developer background checks
- Screening requirements
- Access management
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    DeveloperScreening,
    ScreeningStatus,
    ScreeningType,
)


class DeveloperScreeningService:
    """Service for SA-21: Developer Screening"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_screening(
        self,
        developer_name: str,
        screening_type: ScreeningType,
        developer_email: Optional[str] = None,
        developer_role: Optional[str] = None,
        screening_requirements: Optional[List[str]] = None,
        screened_by: Optional[str] = None,
        screening_agency: Optional[str] = None,
    ) -> DeveloperScreening:
        """Create a developer screening"""
        screening = DeveloperScreening(
            developer_name=developer_name,
            developer_email=developer_email,
            developer_role=developer_role,
            screening_type=screening_type.value,
            screening_requirements=screening_requirements,
            screened_by=screened_by,
            screening_agency=screening_agency,
            status=ScreeningStatus.PENDING.value,
        )
        self.db.add(screening)
        self.db.commit()
        self.db.refresh(screening)
        return screening
    
    def update_screening_status(
        self,
        screening_id: int,
        status: ScreeningStatus,
        passed: Optional[bool] = None,
        findings: Optional[List[Dict[str, Any]]] = None,
        adverse_findings: bool = False,
        adverse_findings_description: Optional[str] = None,
    ) -> DeveloperScreening:
        """Update screening status"""
        screening = self.db.query(DeveloperScreening).filter(
            DeveloperScreening.id == screening_id
        ).first()
        if not screening:
            raise ValueError(f"Screening {screening_id} not found")
        
        screening.status = status.value
        
        if passed is not None:
            screening.passed = passed
        
        if findings:
            screening.findings = findings
        
        screening.adverse_findings = adverse_findings
        if adverse_findings_description:
            screening.adverse_findings_description = adverse_findings_description
        
        if status == ScreeningStatus.COMPLETED:
            screening.screening_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(screening)
        return screening
    
    def grant_access(
        self,
        screening_id: int,
        access_level: str,
        granted_by: str,
        valid_until_date: Optional[datetime] = None,
        requires_renewal: bool = False,
        renewal_interval_days: Optional[int] = None,
    ) -> DeveloperScreening:
        """Grant access based on screening"""
        screening = self.db.query(DeveloperScreening).filter(
            DeveloperScreening.id == screening_id
        ).first()
        if not screening:
            raise ValueError(f"Screening {screening_id} not found")
        
        if not screening.passed:
            raise ValueError("Access cannot be granted for failed screening")
        
        screening.access_granted = True
        screening.access_level = access_level
        screening.access_granted_by = granted_by
        screening.access_granted_date = datetime.utcnow()
        screening.valid_until_date = valid_until_date
        screening.requires_renewal = requires_renewal
        screening.renewal_interval_days = renewal_interval_days
        
        self.db.commit()
        self.db.refresh(screening)
        return screening
    
    def revoke_access(
        self,
        screening_id: int,
        notes: Optional[str] = None,
    ) -> DeveloperScreening:
        """Revoke access"""
        screening = self.db.query(DeveloperScreening).filter(
            DeveloperScreening.id == screening_id
        ).first()
        if not screening:
            raise ValueError(f"Screening {screening_id} not found")
        
        screening.access_granted = False
        screening.access_level = None
        if notes:
            screening.notes = (screening.notes or "") + f"\nAccess revoked: {notes}"
        
        self.db.commit()
        self.db.refresh(screening)
        return screening
    
    def check_renewals(self) -> List[DeveloperScreening]:
        """Check for screenings requiring renewal"""
        now = datetime.utcnow()
        cutoff = now + timedelta(days=30)  # Check 30 days ahead
        
        screenings_to_renew = self.db.query(DeveloperScreening).filter(
            and_(
                DeveloperScreening.requires_renewal == True,
                DeveloperScreening.valid_until_date.isnot(None),
                DeveloperScreening.valid_until_date <= cutoff,
                DeveloperScreening.access_granted == True,
            )
        ).all()
        
        return screenings_to_renew
    
    def list_screenings(
        self,
        developer_email: Optional[str] = None,
        screening_type: Optional[ScreeningType] = None,
        status: Optional[ScreeningStatus] = None,
        access_granted: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DeveloperScreening], int]:
        """List developer screenings"""
        query = self.db.query(DeveloperScreening)
        
        if developer_email:
            query = query.filter(DeveloperScreening.developer_email == developer_email)
        
        if screening_type:
            query = query.filter(DeveloperScreening.screening_type == screening_type.value)
        
        if status:
            query = query.filter(DeveloperScreening.status == status.value)
        
        if access_granted is not None:
            query = query.filter(DeveloperScreening.access_granted == access_granted)
        
        total = query.count()
        screenings = query.order_by(desc(DeveloperScreening.created_at)).offset(offset).limit(limit).all()
        
        return screenings, total
    
    def get_screening_summary(self, developer_email: Optional[str] = None) -> Dict[str, Any]:
        """Get screening summary"""
        query = self.db.query(DeveloperScreening)
        
        if developer_email:
            query = query.filter(DeveloperScreening.developer_email == developer_email)
        
        screenings = screenings = query.all()
        
        return {
            "total_screenings": len(screenings),
            "by_status": self._summarize_by_status(screenings),
            "by_type": self._summarize_by_type(screenings),
            "access_granted": sum(1 for s in screenings if s.access_granted),
            "pending_renewal": len(self.check_renewals()),
        }
    
    def _summarize_by_status(self, screenings: List[DeveloperScreening]) -> Dict[str, int]:
        """Summarize by status"""
        summary = {}
        for screening in screenings:
            status = screening.status
            summary[status] = summary.get(status, 0) + 1
        return summary
    
    def _summarize_by_type(self, screenings: List[DeveloperScreening]) -> Dict[str, int]:
        """Summarize by type"""
        summary = {}
        for screening in screenings:
            s_type = screening.screening_type
            summary[s_type] = summary.get(s_type, 0) + 1
        return summary
