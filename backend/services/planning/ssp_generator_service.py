"""
PL-2: System Security Plan (SSP) Generator Service

Auto-generates SSP documents from system state with:
- Section builders for all 18 control families
- Evidence collection
- Version management
- Document generation (PDF)
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
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

from core.logger import logger
from models.planning import (
    SystemSecurityPlan, SSPControlSection, SSPVersion,
    SSPStatus, ControlFamily
)
from models.user import User


class SSPGeneratorService:
    """
    PL-2: System Security Plan Generator
    
    Generates comprehensive SSP documents with all control families.
    """
    
    # FedRAMP control families (18 total)
    CONTROL_FAMILIES = [
        ControlFamily.AC, ControlFamily.AT, ControlFamily.AU, ControlFamily.CA,
        ControlFamily.CM, ControlFamily.CP, ControlFamily.IA, ControlFamily.IR,
        ControlFamily.MA, ControlFamily.MP, ControlFamily.PE, ControlFamily.PL,
        ControlFamily.PS, ControlFamily.RA, ControlFamily.SA, ControlFamily.SC,
        ControlFamily.SI, ControlFamily.SR
    ]
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_ssp(
        self,
        ssp_name: str,
        system_name: str,
        system_id: Optional[str] = None,
        system_description: Optional[str] = None,
        system_owner: Optional[str] = None,
        **kwargs
    ) -> SystemSecurityPlan:
        """
        Create a new System Security Plan.
        """
        # Generate system ID if not provided
        if not system_id:
            system_id = f"SYS-{self.org_id}-{int(datetime.now(timezone.utc).timestamp())}"
        
        ssp = SystemSecurityPlan(
            org_id=self.org_id,
            ssp_name=ssp_name,
            system_name=system_name,
            system_id=system_id,
            system_description=system_description or f"Security plan for {system_name}",
            system_owner=system_owner,
            version="1.0",
            status=SSPStatus.DRAFT.value,
            is_active=False,
            control_implementations={},
            created_by_user_id=self.user_id,
        )
        
        self.db.add(ssp)
        self.db.commit()
        self.db.refresh(ssp)
        
        logger.info(f"Created SSP {ssp.id} for system {system_name}")
        
        return ssp
    
    def add_control_section(
        self,
        ssp_id: str,
        control_family: str,
        control_id: str,
        control_title: str,
        implementation_description: str,
        implementation_status: str = "planned",
        **kwargs
    ) -> SSPControlSection:
        """
        Add a control section to the SSP.
        """
        ssp = self.db.query(SystemSecurityPlan).filter(
            SystemSecurityPlan.id == ssp_id,
            SystemSecurityPlan.org_id == self.org_id
        ).first()
        
        if not ssp:
            raise ValueError(f"SSP {ssp_id} not found")
        
        section = SSPControlSection(
            ssp_id=ssp_id,
            control_family=control_family,
            control_id=control_id,
            control_title=control_title,
            implementation_description=implementation_description,
            implementation_status=implementation_status,
            **kwargs
        )
        
        self.db.add(section)
        
        # Update control_implementations JSON
        if ssp.control_implementations is None:
            ssp.control_implementations = {}
        
        if control_family not in ssp.control_implementations:
            ssp.control_implementations[control_family] = {}
        
        ssp.control_implementations[control_family][control_id] = {
            "title": control_title,
            "status": implementation_status,
            "section_id": str(section.id)
        }
        
        self.db.commit()
        self.db.refresh(section)
        
        logger.info(f"Added control section {control_family}-{control_id} to SSP {ssp_id}")
        
        return section
    
    def generate_ssp_document(self, ssp_id: str) -> bytes:
        """
        Generate PDF document for SSP.
        
        Creates comprehensive SSP document with all sections.
        """
        ssp = self.db.query(SystemSecurityPlan).filter(
            SystemSecurityPlan.id == ssp_id,
            SystemSecurityPlan.org_id == self.org_id
        ).first()
        
        if not ssp:
            raise ValueError(f"SSP {ssp_id} not found")
        
        # Get all control sections
        sections = self.db.query(SSPControlSection).filter(
            SSPControlSection.ssp_id == ssp_id
        ).order_by(
            SSPControlSection.control_family,
            SSPControlSection.control_id
        ).all()
        
        # Generate PDF
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
            'SSPTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'SSPHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=12
        )
        
        subheading_style = ParagraphStyle(
            'SSPSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=10
        )
        
        body_style = ParagraphStyle(
            'SSPBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # Title page
        elements.append(Paragraph("SYSTEM SECURITY PLAN", title_style))
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(f"System: {ssp.system_name}", heading_style))
        elements.append(Paragraph(f"System ID: {ssp.system_id or 'N/A'}", body_style))
        elements.append(Paragraph(f"Version: {ssp.version}", body_style))
        elements.append(Paragraph(f"Status: {ssp.status.upper()}", body_style))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", body_style))
        
        if ssp.system_owner:
            elements.append(Paragraph(f"System Owner: {ssp.system_owner}", body_style))
        
        elements.append(PageBreak())
        
        # Table of Contents
        elements.append(Paragraph("TABLE OF CONTENTS", heading_style))
        toc_items = [
            ("1. System Overview", 2),
            ("2. System Description", 2),
            ("3. System Boundaries", 2),
            ("4. Control Implementations", 2),
        ]
        
        # Add control families to TOC
        for i, family in enumerate(self.CONTROL_FAMILIES, start=5):
            family_name = self._get_family_name(family.value)
            toc_items.append((f"{i}. {family_name} Controls", 2))
        
        toc_data = [[item[0], ""] for item in toc_items]
        toc_table = Table(toc_data, colWidths=[5*inch, 1*inch])
        toc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(toc_table)
        elements.append(PageBreak())
        
        # System Overview
        elements.append(Paragraph("1. SYSTEM OVERVIEW", heading_style))
        elements.append(Paragraph(ssp.system_description or "No description provided.", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # System Description
        elements.append(Paragraph("2. SYSTEM DESCRIPTION", heading_style))
        if ssp.system_description:
            elements.append(Paragraph(ssp.system_description, body_style))
        else:
            elements.append(Paragraph("System description to be provided.", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # System Boundaries
        elements.append(Paragraph("3. SYSTEM BOUNDARIES", heading_style))
        if ssp.authorization_boundary:
            elements.append(Paragraph(ssp.authorization_boundary, body_style))
        else:
            elements.append(Paragraph("Authorization boundary description to be provided.", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Control Implementations Overview
        elements.append(Paragraph("4. CONTROL IMPLEMENTATIONS", heading_style))
        elements.append(Paragraph(
            f"This SSP documents the implementation of security controls across {len(self.CONTROL_FAMILIES)} control families. "
            "Each control family section provides detailed implementation descriptions, status, and evidence.",
            body_style
        ))
        elements.append(PageBreak())
        
        # Control Family Sections
        current_family = None
        section_num = 5
        
        for section in sections:
            if section.control_family != current_family:
                if current_family is not None:
                    elements.append(PageBreak())
                
                current_family = section.control_family
                family_name = self._get_family_name(current_family)
                elements.append(Paragraph(f"{section_num}. {family_name} CONTROLS", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                section_num += 1
            
            # Control subsection
            control_title = section.control_title or f"{section.control_family}-{section.control_id}"
            elements.append(Paragraph(
                f"{section.control_family}-{section.control_id}: {control_title}",
                subheading_style
            ))
            
            # Implementation status
            status_text = f"<b>Implementation Status:</b> {section.implementation_status.upper()}"
            elements.append(Paragraph(status_text, body_style))
            elements.append(Spacer(1, 0.05*inch))
            
            # Implementation description
            elements.append(Paragraph("<b>Implementation Description:</b>", body_style))
            elements.append(Paragraph(section.implementation_description, body_style))
            elements.append(Spacer(1, 0.1*inch))
            
            # Implementation narrative if available
            if section.implementation_narrative:
                elements.append(Paragraph("<b>Implementation Narrative:</b>", body_style))
                elements.append(Paragraph(section.implementation_narrative, body_style))
                elements.append(Spacer(1, 0.1*inch))
            
            # Responsible party
            if section.responsible_party or section.responsible_role:
                resp_text = "<b>Responsible Party:</b> "
                if section.responsible_role:
                    resp_text += f"Role: {section.responsible_role}"
                if section.responsible_party:
                    if section.responsible_role:
                        resp_text += ", "
                    resp_text += f"Party: {section.responsible_party}"
                elements.append(Paragraph(resp_text, body_style))
                elements.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        
        logger.info(f"Generated SSP document for {ssp_id}, size: {len(pdf_bytes)} bytes")
        
        return pdf_bytes
    
    def collect_evidence(self, ssp_id: str) -> Dict[str, Any]:
        """
        Collect evidence artifacts for SSP.
        
        Aggregates evidence from various sources (audit logs, configurations, etc.)
        """
        ssp = self.db.query(SystemSecurityPlan).filter(
            SystemSecurityPlan.id == ssp_id,
            SystemSecurityPlan.org_id == self.org_id
        ).first()
        
        if not ssp:
            raise ValueError(f"SSP {ssp_id} not found")
        
        evidence = {
            "ssp_id": str(ssp.id),
            "system_name": ssp.system_name,
            "collection_date": datetime.now(timezone.utc).isoformat(),
            "evidence_sources": [],
            "control_evidence": {}
        }
        
        # Collect evidence from control sections
        sections = self.db.query(SSPControlSection).filter(
            SSPControlSection.ssp_id == ssp_id
        ).all()
        
        for section in sections:
            control_key = f"{section.control_family}-{section.control_id}"
            evidence["control_evidence"][control_key] = {
                "section_id": str(section.id),
                "evidence_references": section.evidence_references or [],
                "test_procedures": section.test_procedures,
                "test_results": section.test_results or {}
            }
        
        # TODO: Collect additional evidence from:
        # - Audit logs (AU controls)
        # - Configuration baselines (CM controls)
        # - Access control records (AC controls)
        # - Incident records (IR controls)
        # - etc.
        
        return evidence
    
    def create_version(
        self,
        ssp_id: str,
        version_number: str,
        change_summary: Optional[str] = None,
        changes_made: Optional[List[Dict]] = None
    ) -> SSPVersion:
        """
        Create a new version of the SSP.
        """
        ssp = self.db.query(SystemSecurityPlan).filter(
            SystemSecurityPlan.id == ssp_id,
            SystemSecurityPlan.org_id == self.org_id
        ).first()
        
        if not ssp:
            raise ValueError(f"SSP {ssp_id} not found")
        
        version = SSPVersion(
            ssp_id=ssp_id,
            version_number=version_number,
            change_summary=change_summary,
            changes_made=changes_made or [],
            created_by_user_id=self.user_id
        )
        
        self.db.add(version)
        
        # Update SSP version
        ssp.version = version_number
        ssp.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(version)
        
        logger.info(f"Created version {version_number} for SSP {ssp_id}")
        
        return version
    
    def approve_ssp(
        self,
        ssp_id: str,
        approval_notes: Optional[str] = None
    ) -> SystemSecurityPlan:
        """
        Approve the SSP.
        """
        ssp = self.db.query(SystemSecurityPlan).filter(
            SystemSecurityPlan.id == ssp_id,
            SystemSecurityPlan.org_id == self.org_id
        ).first()
        
        if not ssp:
            raise ValueError(f"SSP {ssp_id} not found")
        
        ssp.status = SSPStatus.APPROVED.value
        ssp.is_active = True
        ssp.approved_by_user_id = self.user_id
        ssp.approved_at = datetime.now(timezone.utc)
        ssp.approval_notes = approval_notes
        ssp.effective_date = datetime.now(timezone.utc)
        
        if not ssp.next_review_date:
            ssp.next_review_date = datetime.now(timezone.utc) + timedelta(days=ssp.review_frequency_days)
        
        self.db.commit()
        self.db.refresh(ssp)
        
        logger.info(f"Approved SSP {ssp_id}")
        
        return ssp
    
    def _get_family_name(self, family_code: str) -> str:
        """Get human-readable name for control family"""
        family_names = {
            "AC": "Access Control",
            "AT": "Awareness and Training",
            "AU": "Audit and Accountability",
            "CA": "Assessment and Authorization",
            "CM": "Configuration Management",
            "CP": "Contingency Planning",
            "IA": "Identification and Authentication",
            "IR": "Incident Response",
            "MA": "Maintenance",
            "MP": "Media Protection",
            "PE": "Physical and Environmental Protection",
            "PL": "Planning",
            "PS": "Personnel Security",
            "RA": "Risk Assessment",
            "SA": "System and Services Acquisition",
            "SC": "System and Communications Protection",
            "SI": "System and Information Integrity",
            "SR": "Supply Chain Risk Management",
        }
        return family_names.get(family_code, family_code)
