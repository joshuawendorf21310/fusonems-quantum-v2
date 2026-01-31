"""
CA-3: System Interconnections Service

Manages ISA/MOU documents and interconnection approvals.
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from core.logger import logger
from models.assessment import SystemInterconnection, InterconnectionStatus, InterconnectionType


class InterconnectionService:
    """
    CA-3: System Interconnections Service
    
    Manages system interconnections and ISA/MOU documents.
    """
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_interconnection(
        self,
        interconnection_name: str,
        system_id: str,
        system_name: str,
        connected_system_id: str,
        connected_system_name: str,
        interconnection_type: str,
        purpose: str,
        data_types_exchanged: Optional[List[str]] = None,
        **kwargs
    ) -> SystemInterconnection:
        """
        Create a new system interconnection.
        """
        interconnection_number = f"IC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._get_next_interconnection_number()}"
        
        interconnection = SystemInterconnection(
            org_id=self.org_id,
            interconnection_name=interconnection_name,
            interconnection_number=interconnection_number,
            system_id=system_id,
            system_name=system_name,
            connected_system_id=connected_system_id,
            connected_system_name=connected_system_name,
            interconnection_type=interconnection_type,
            purpose=purpose,
            data_types_exchanged=data_types_exchanged or [],
            status=InterconnectionStatus.PROPOSED.value,
            proposed_by_user_id=self.user_id,
            proposed_at=datetime.now(timezone.utc),
            review_frequency_days=365,
            **kwargs
        )
        
        self.db.add(interconnection)
        self.db.commit()
        self.db.refresh(interconnection)
        
        logger.info(f"Created interconnection {interconnection.id}: {interconnection_name}")
        
        return interconnection
    
    def generate_isa_document(self, interconnection_id: str) -> bytes:
        """
        Generate Interconnection Security Agreement (ISA) document.
        """
        interconnection = self.db.query(SystemInterconnection).filter(
            SystemInterconnection.id == interconnection_id,
            SystemInterconnection.org_id == self.org_id
        ).first()
        
        if not interconnection:
            raise ValueError(f"Interconnection {interconnection_id} not found")
        
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
            'ISATitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'ISAHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'ISABody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # Title
        elements.append(Paragraph("INTERCONNECTION SECURITY AGREEMENT", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Parties
        elements.append(Paragraph("PARTIES", heading_style))
        elements.append(Paragraph(f"System 1: {interconnection.system_name} ({interconnection.system_id})", body_style))
        elements.append(Paragraph(f"System 2: {interconnection.connected_system_name} ({interconnection.connected_system_id})", body_style))
        if interconnection.connected_organization:
            elements.append(Paragraph(f"Organization: {interconnection.connected_organization}", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Purpose
        elements.append(Paragraph("PURPOSE", heading_style))
        elements.append(Paragraph(interconnection.purpose, body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Data Types
        elements.append(Paragraph("DATA TYPES EXCHANGED", heading_style))
        if interconnection.data_types_exchanged:
            for data_type in interconnection.data_types_exchanged:
                elements.append(Paragraph(f"• {data_type}", body_style))
        else:
            elements.append(Paragraph("Data types to be specified.", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Security Requirements
        elements.append(Paragraph("SECURITY REQUIREMENTS", heading_style))
        if interconnection.security_requirements:
            for req in interconnection.security_requirements:
                elements.append(Paragraph(f"• {req}", body_style))
        else:
            elements.append(Paragraph("Security requirements to be specified.", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Security Controls
        elements.append(Paragraph("SECURITY CONTROLS", heading_style))
        if interconnection.security_controls:
            for control in interconnection.security_controls:
                elements.append(Paragraph(f"• {control}", body_style))
        else:
            elements.append(Paragraph("Security controls to be specified.", body_style))
        
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        
        logger.info(f"Generated ISA document for interconnection {interconnection_id}")
        
        return pdf_bytes
    
    def approve_interconnection(self, interconnection_id: str) -> SystemInterconnection:
        """
        Approve the interconnection.
        """
        interconnection = self.db.query(SystemInterconnection).filter(
            SystemInterconnection.id == interconnection_id,
            SystemInterconnection.org_id == self.org_id
        ).first()
        
        if not interconnection:
            raise ValueError(f"Interconnection {interconnection_id} not found")
        
        interconnection.status = InterconnectionStatus.APPROVED.value
        interconnection.approved_by_user_id = self.user_id
        interconnection.approved_at = datetime.now(timezone.utc)
        interconnection.effective_date = datetime.now(timezone.utc)
        
        if not interconnection.next_review_date:
            interconnection.next_review_date = datetime.now(timezone.utc) + timedelta(days=interconnection.review_frequency_days)
        
        self.db.commit()
        self.db.refresh(interconnection)
        
        logger.info(f"Approved interconnection {interconnection_id}")
        
        return interconnection
    
    def _get_next_interconnection_number(self) -> str:
        """Get next sequential interconnection number"""
        today = datetime.now(timezone.utc).date()
        count = self.db.query(SystemInterconnection).filter(
            SystemInterconnection.org_id == self.org_id,
            func.date(SystemInterconnection.created_at) == today
        ).count() or 0
        return f"{count + 1:03d}"
