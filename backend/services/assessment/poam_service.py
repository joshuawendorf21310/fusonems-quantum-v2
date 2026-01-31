"""
CA-5: Plan of Action & Milestones (POA&M) Service

Auto-generates POA&M from findings with milestone tracking and risk scoring.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from core.logger import logger
from models.assessment import POAMItem, POAMStatus, POAMPriority
from models.assessment import AssessmentFinding


class POAMService:
    """
    CA-5: Plan of Action & Milestones Service
    
    Manages POA&M items with auto-generation from findings.
    """
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_poam_from_finding(
        self,
        finding_id: str,
        remediation_plan: str,
        remediation_steps: Optional[List[str]] = None,
        scheduled_completion_date: Optional[datetime] = None,
        responsible_party: Optional[str] = None,
        **kwargs
    ) -> POAMItem:
        """
        Auto-generate POA&M item from assessment finding.
        """
        finding = self.db.query(AssessmentFinding).filter(
            AssessmentFinding.id == finding_id
        ).first()
        
        if not finding:
            raise ValueError(f"Finding {finding_id} not found")
        
        # Calculate risk score based on severity
        risk_score = self._calculate_risk_score(finding.severity)
        
        # Determine priority from severity
        priority = self._severity_to_priority(finding.severity)
        
        # Generate POA&M ID
        poam_id = f"POAM-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._get_next_poam_number()}"
        
        poam = POAMItem(
            org_id=self.org_id,
            poam_id=poam_id,
            title=finding.title,
            description=finding.description,
            finding_id=finding_id,
            assessment_id=finding.assessment_id,
            control_family=finding.control_family,
            control_id=finding.control_id,
            severity=finding.severity,
            priority=priority,
            risk_score=risk_score,
            remediation_plan=remediation_plan,
            remediation_steps=remediation_steps or [],
            scheduled_completion_date=scheduled_completion_date,
            responsible_party=responsible_party,
            status=POAMStatus.OPEN.value,
            created_by_user_id=self.user_id,
            **kwargs
        )
        
        self.db.add(poam)
        
        # Update finding with POA&M reference
        finding.poam_id = poam_id
        
        self.db.commit()
        self.db.refresh(poam)
        
        logger.info(f"Created POA&M {poam_id} from finding {finding_id}")
        
        return poam
    
    def create_poam(
        self,
        title: str,
        description: str,
        severity: str,
        remediation_plan: str,
        control_family: Optional[str] = None,
        control_id: Optional[str] = None,
        **kwargs
    ) -> POAMItem:
        """
        Create a new POA&M item manually.
        """
        risk_score = self._calculate_risk_score(severity)
        priority = self._severity_to_priority(severity)
        
        poam_id = f"POAM-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._get_next_poam_number()}"
        
        poam = POAMItem(
            org_id=self.org_id,
            poam_id=poam_id,
            title=title,
            description=description,
            control_family=control_family,
            control_id=control_id,
            severity=severity,
            priority=priority,
            risk_score=risk_score,
            remediation_plan=remediation_plan,
            status=POAMStatus.OPEN.value,
            created_by_user_id=self.user_id,
            **kwargs
        )
        
        self.db.add(poam)
        self.db.commit()
        self.db.refresh(poam)
        
        logger.info(f"Created POA&M {poam_id}: {title}")
        
        return poam
    
    def update_poam_status(
        self,
        poam_id: str,
        status: str,
        progress_percent: Optional[float] = None,
        progress_notes: Optional[str] = None
    ) -> POAMItem:
        """
        Update POA&M status and progress.
        """
        poam = self.db.query(POAMItem).filter(
            POAMItem.poam_id == poam_id,
            POAMItem.org_id == self.org_id
        ).first()
        
        if not poam:
            raise ValueError(f"POA&M {poam_id} not found")
        
        poam.status = status
        if progress_percent is not None:
            poam.progress_percent = progress_percent
        if progress_notes:
            poam.progress_notes = progress_notes
        
        # Record status update
        if poam.status_updates is None:
            poam.status_updates = []
        
        poam.status_updates.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "progress_percent": progress_percent,
            "notes": progress_notes,
            "updated_by": self.user_id
        })
        
        # Mark as completed if status is completed
        if status == POAMStatus.COMPLETED.value:
            poam.actual_completion_date = datetime.now(timezone.utc)
            poam.progress_percent = 100.0
        
        self.db.commit()
        self.db.refresh(poam)
        
        logger.info(f"Updated POA&M {poam_id} status to {status}")
        
        return poam
    
    def generate_poam_report(self, include_completed: bool = False) -> bytes:
        """
        Generate POA&M report with all open items.
        """
        query = self.db.query(POAMItem).filter(
            POAMItem.org_id == self.org_id
        )
        
        if not include_completed:
            query = query.filter(POAMItem.status != POAMStatus.COMPLETED.value)
        
        poam_items = query.order_by(
            POAMItem.priority.desc(),
            POAMItem.scheduled_completion_date
        ).all()
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
        )
        
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle(
            'POAMTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'POAMHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'POAMBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # Title
        elements.append(Paragraph("PLAN OF ACTION & MILESTONES (POA&M)", title_style))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", body_style))
        elements.append(PageBreak())
        
        # Summary
        elements.append(Paragraph("SUMMARY", heading_style))
        summary_data = [
            ["Status", "Count"],
            ["Open", str(len([p for p in poam_items if p.status == POAMStatus.OPEN.value]))],
            ["In Progress", str(len([p for p in poam_items if p.status == POAMStatus.IN_PROGRESS.value]))],
            ["On Hold", str(len([p for p in poam_items if p.status == POAMStatus.ON_HOLD.value]))],
            ["Completed", str(len([p for p in poam_items if p.status == POAMStatus.COMPLETED.value]))],
            ["Total", str(len(poam_items))],
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(PageBreak())
        
        # POA&M Items
        elements.append(Paragraph("POA&M ITEMS", heading_style))
        for i, poam in enumerate(poam_items, 1):
            elements.append(Paragraph(f"{i}. {poam.poam_id}: {poam.title}", heading_style))
            elements.append(Paragraph(f"Status: {poam.status.upper()}", body_style))
            elements.append(Paragraph(f"Severity: {poam.severity.upper()} | Priority: {poam.priority.upper()}", body_style))
            if poam.control_family and poam.control_id:
                elements.append(Paragraph(f"Control: {poam.control_family}-{poam.control_id}", body_style))
            elements.append(Paragraph(f"Description: {poam.description}", body_style))
            elements.append(Paragraph(f"Remediation Plan: {poam.remediation_plan}", body_style))
            if poam.scheduled_completion_date:
                elements.append(Paragraph(f"Scheduled Completion: {poam.scheduled_completion_date.strftime('%Y-%m-%d')}", body_style))
            elements.append(Paragraph(f"Progress: {poam.progress_percent}%", body_style))
            if poam.responsible_party:
                elements.append(Paragraph(f"Responsible Party: {poam.responsible_party}", body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        
        logger.info(f"Generated POA&M report with {len(poam_items)} items")
        
        return pdf_bytes
    
    def _calculate_risk_score(self, severity: str) -> float:
        """Calculate risk score from severity"""
        severity_scores = {
            "critical": 10.0,
            "high": 7.5,
            "medium": 5.0,
            "low": 2.5
        }
        return severity_scores.get(severity.lower(), 5.0)
    
    def _severity_to_priority(self, severity: str) -> str:
        """Convert severity to priority"""
        mapping = {
            "critical": POAMPriority.CRITICAL.value,
            "high": POAMPriority.HIGH.value,
            "medium": POAMPriority.MEDIUM.value,
            "low": POAMPriority.LOW.value
        }
        return mapping.get(severity.lower(), POAMPriority.MEDIUM.value)
    
    def _get_next_poam_number(self) -> str:
        """Get next sequential POA&M number"""
        today = datetime.now(timezone.utc).date()
        count = self.db.query(POAMItem).filter(
            POAMItem.org_id == self.org_id,
            func.date(POAMItem.created_at) == today
        ).count() or 0
        return f"{count + 1:03d}"
