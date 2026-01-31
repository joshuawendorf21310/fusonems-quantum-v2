"""
CA-2: Security Assessment Service

Manages security assessments including control testing automation and results documentation.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
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
from models.assessment import (
    SecurityAssessment, ControlTest, AssessmentFinding,
    AssessmentStatus, AssessmentType, ControlTestResult
)


class SecurityAssessmentService:
    """
    CA-2: Security Assessment Service
    
    Manages security assessments and control testing.
    """
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_assessment(
        self,
        assessment_name: str,
        assessment_type: str,
        scope_description: Optional[str] = None,
        systems_in_scope: Optional[List[str]] = None,
        planned_start_date: Optional[datetime] = None,
        planned_end_date: Optional[datetime] = None,
        **kwargs
    ) -> SecurityAssessment:
        """
        Create a new security assessment.
        """
        # Generate assessment number
        assessment_number = f"ASSESS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._get_next_assessment_number()}"
        
        assessment = SecurityAssessment(
            org_id=self.org_id,
            assessment_name=assessment_name,
            assessment_number=assessment_number,
            assessment_type=assessment_type,
            scope_description=scope_description,
            systems_in_scope=systems_in_scope or [],
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date,
            status=AssessmentStatus.PLANNED.value,
            created_by_user_id=self.user_id,
            **kwargs
        )
        
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        
        logger.info(f"Created Security Assessment {assessment.id}: {assessment_name}")
        
        return assessment
    
    def add_control_test(
        self,
        assessment_id: str,
        control_family: str,
        control_id: str,
        control_title: str,
        test_procedure: Optional[str] = None,
        test_method: Optional[str] = None,
        **kwargs
    ) -> ControlTest:
        """
        Add a control test to the assessment.
        """
        assessment = self.db.query(SecurityAssessment).filter(
            SecurityAssessment.id == assessment_id,
            SecurityAssessment.org_id == self.org_id
        ).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        test = ControlTest(
            assessment_id=assessment_id,
            control_family=control_family,
            control_id=control_id,
            control_title=control_title,
            test_procedure=test_procedure,
            test_method=test_method or "examine",
            test_result=ControlTestResult.NOT_TESTED.value,
            **kwargs
        )
        
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)
        
        logger.info(f"Added control test {control_family}-{control_id} to assessment {assessment_id}")
        
        return test
    
    def record_test_result(
        self,
        test_id: str,
        test_result: str,
        test_notes: Optional[str] = None,
        evidence_collected: Optional[List[str]] = None,
        findings_identified: Optional[List[str]] = None
    ) -> ControlTest:
        """
        Record test results for a control test.
        """
        test = self.db.query(ControlTest).join(SecurityAssessment).filter(
            ControlTest.id == test_id,
            SecurityAssessment.org_id == self.org_id
        ).first()
        
        if not test:
            raise ValueError(f"Control test {test_id} not found")
        
        test.test_result = test_result
        test.test_notes = test_notes
        test.evidence_collected = evidence_collected or []
        test.findings_identified = findings_identified or []
        test.tested_by_user_id = self.user_id
        test.tested_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(test)
        
        logger.info(f"Recorded test result for {test_id}: {test_result}")
        
        return test
    
    def add_finding(
        self,
        assessment_id: str,
        title: str,
        description: str,
        severity: str,
        control_family: Optional[str] = None,
        control_id: Optional[str] = None,
        **kwargs
    ) -> AssessmentFinding:
        """
        Add a finding to the assessment.
        """
        assessment = self.db.query(SecurityAssessment).filter(
            SecurityAssessment.id == assessment_id,
            SecurityAssessment.org_id == self.org_id
        ).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        # Generate finding number
        finding_number = f"FIND-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._get_next_finding_number(assessment_id)}"
        
        finding = AssessmentFinding(
            assessment_id=assessment_id,
            finding_number=finding_number,
            title=title,
            description=description,
            severity=severity,
            control_family=control_family,
            control_id=control_id,
            status="open",
            **kwargs
        )
        
        self.db.add(finding)
        
        # Update assessment finding counts
        assessment.findings_count += 1
        if severity == "critical":
            assessment.critical_findings_count += 1
        elif severity == "high":
            assessment.high_findings_count += 1
        elif severity == "medium":
            assessment.medium_findings_count += 1
        elif severity == "low":
            assessment.low_findings_count += 1
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"Added finding {finding_number} to assessment {assessment_id}")
        
        return finding
    
    def generate_assessment_report(self, assessment_id: str) -> bytes:
        """
        Generate PDF assessment report.
        """
        assessment = self.db.query(SecurityAssessment).filter(
            SecurityAssessment.id == assessment_id,
            SecurityAssessment.org_id == self.org_id
        ).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        # Get all control tests
        tests = self.db.query(ControlTest).filter(
            ControlTest.assessment_id == assessment_id
        ).order_by(ControlTest.control_family, ControlTest.control_id).all()
        
        # Get all findings
        findings = self.db.query(AssessmentFinding).filter(
            AssessmentFinding.assessment_id == assessment_id
        ).order_by(
            AssessmentFinding.severity.desc(),
            AssessmentFinding.identified_at
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
        
        # Custom styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'ReportHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # Title page
        elements.append(Paragraph("SECURITY ASSESSMENT REPORT", title_style))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(assessment.assessment_name, heading_style))
        elements.append(Paragraph(f"Assessment Number: {assessment.assessment_number}", body_style))
        elements.append(Paragraph(f"Type: {assessment.assessment_type.upper()}", body_style))
        elements.append(Paragraph(f"Status: {assessment.status.upper()}", body_style))
        if assessment.assessment_date:
            elements.append(Paragraph(f"Assessment Date: {assessment.assessment_date.strftime('%Y-%m-%d')}", body_style))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", body_style))
        elements.append(PageBreak())
        
        # Executive Summary
        elements.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        if assessment.findings_summary:
            elements.append(Paragraph(assessment.findings_summary, body_style))
        else:
            summary_text = (
                f"This security assessment was conducted for {assessment.assessment_type} purposes. "
                f"The assessment included testing of security controls and identified "
                f"{assessment.findings_count} findings across various severity levels."
            )
            elements.append(Paragraph(summary_text, body_style))
        
        # Findings summary table
        findings_data = [
            ["Severity", "Count"],
            ["Critical", str(assessment.critical_findings_count)],
            ["High", str(assessment.high_findings_count)],
            ["Medium", str(assessment.medium_findings_count)],
            ["Low", str(assessment.low_findings_count)],
            ["Total", str(assessment.findings_count)],
        ]
        findings_table = Table(findings_data, colWidths=[2*inch, 1*inch])
        findings_table.setStyle(TableStyle([
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
        elements.append(Spacer(1, 0.1*inch))
        elements.append(findings_table)
        elements.append(PageBreak())
        
        # Control Test Results
        elements.append(Paragraph("CONTROL TEST RESULTS", heading_style))
        if tests:
            tests_data = [["Control", "Test Method", "Result", "Notes"]]
            for test in tests:
                control_id = f"{test.control_family}-{test.control_id}"
                test_method = test.test_method or "N/A"
                result = test.test_result.upper() if test.test_result else "NOT TESTED"
                notes = (test.test_notes[:50] + "...") if test.test_notes and len(test.test_notes) > 50 else (test.test_notes or "N/A")
                tests_data.append([control_id, test_method, result, notes])
            
            tests_table = Table(tests_data, colWidths=[1.5*inch, 1*inch, 1*inch, 2.5*inch])
            tests_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(tests_table)
        else:
            elements.append(Paragraph("No control tests recorded.", body_style))
        elements.append(PageBreak())
        
        # Findings
        elements.append(Paragraph("ASSESSMENT FINDINGS", heading_style))
        if findings:
            for i, finding in enumerate(findings, 1):
                elements.append(Paragraph(f"{i}. {finding.finding_number}: {finding.title}", heading_style))
                elements.append(Paragraph(f"Severity: {finding.severity.upper()}", body_style))
                if finding.control_family and finding.control_id:
                    elements.append(Paragraph(f"Related Control: {finding.control_family}-{finding.control_id}", body_style))
                elements.append(Paragraph(f"Description: {finding.description}", body_style))
                if finding.recommendation:
                    elements.append(Paragraph(f"Recommendation: {finding.recommendation}", body_style))
                elements.append(Spacer(1, 0.2*inch))
        else:
            elements.append(Paragraph("No findings identified.", body_style))
        
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        
        logger.info(f"Generated assessment report for {assessment_id}")
        
        return pdf_bytes
    
    def complete_assessment(
        self,
        assessment_id: str,
        overall_result: str,
        findings_summary: Optional[str] = None
    ) -> SecurityAssessment:
        """
        Complete the assessment.
        """
        assessment = self.db.query(SecurityAssessment).filter(
            SecurityAssessment.id == assessment_id,
            SecurityAssessment.org_id == self.org_id
        ).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        assessment.status = AssessmentStatus.COMPLETED.value
        assessment.overall_result = overall_result
        assessment.findings_summary = findings_summary
        assessment.actual_end_date = datetime.now(timezone.utc)
        
        # Set next assessment due date (typically 1 year for annual assessments)
        if assessment.assessment_type == AssessmentType.ANNUAL.value:
            assessment.next_assessment_due = datetime.now(timezone.utc) + timedelta(days=365)
        
        self.db.commit()
        self.db.refresh(assessment)
        
        logger.info(f"Completed assessment {assessment_id} with result: {overall_result}")
        
        return assessment
    
    def _get_next_assessment_number(self) -> str:
        """Get next sequential assessment number"""
        today = datetime.now(timezone.utc).date()
        count = self.db.query(func.count(SecurityAssessment.id)).filter(
            SecurityAssessment.org_id == self.org_id,
            func.date(SecurityAssessment.created_at) == today
        ).scalar() or 0
        return f"{count + 1:03d}"
    
    def _get_next_finding_number(self, assessment_id: str) -> str:
        """Get next sequential finding number for assessment"""
        count = self.db.query(func.count(AssessmentFinding.id)).filter(
            AssessmentFinding.assessment_id == assessment_id
        ).scalar() or 0
        return f"{count + 1:03d}"
