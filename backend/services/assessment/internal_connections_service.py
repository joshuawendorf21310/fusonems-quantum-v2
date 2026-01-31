"""
CA-9: Internal System Connections Service

Manages internal system connections with security requirements and approval workflow.
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
from models.assessment import InternalSystemConnection, InternalConnectionStatus


class InternalConnectionsService:
    """
    CA-9: Internal System Connections Service
    
    Manages internal connections between systems.
    """
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_internal_connection(
        self,
        connection_name: str,
        source_system_id: str,
        source_system_name: str,
        target_system_id: str,
        target_system_name: str,
        connection_type: str,
        purpose: str,
        data_types_exchanged: Optional[List[str]] = None,
        **kwargs
    ) -> InternalSystemConnection:
        """
        Create a new internal system connection.
        """
        connection_number = f"ICONN-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._get_next_connection_number()}"
        
        connection = InternalSystemConnection(
            org_id=self.org_id,
            connection_name=connection_name,
            connection_number=connection_number,
            source_system_id=source_system_id,
            source_system_name=source_system_name,
            target_system_id=target_system_id,
            target_system_name=target_system_name,
            connection_type=connection_type,
            purpose=purpose,
            data_types_exchanged=data_types_exchanged or [],
            status=InternalConnectionStatus.PROPOSED.value,
            proposed_by_user_id=self.user_id,
            proposed_at=datetime.now(timezone.utc),
            **kwargs
        )
        
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        
        logger.info(f"Created internal connection {connection.id}: {connection_name}")
        
        return connection
    
    def approve_connection(self, connection_id: str) -> InternalSystemConnection:
        """
        Approve the internal connection.
        """
        connection = self.db.query(InternalSystemConnection).filter(
            InternalSystemConnection.id == connection_id,
            InternalSystemConnection.org_id == self.org_id
        ).first()
        
        if not connection:
            raise ValueError(f"Internal connection {connection_id} not found")
        
        connection.status = InternalConnectionStatus.APPROVED.value
        connection.approved_by_user_id = self.user_id
        connection.approved_at = datetime.now(timezone.utc)
        connection.effective_date = datetime.now(timezone.utc)
        
        if not connection.next_review_date:
            connection.next_review_date = datetime.now(timezone.utc) + timedelta(days=365)
        
        self.db.commit()
        self.db.refresh(connection)
        
        logger.info(f"Approved internal connection {connection_id}")
        
        return connection
    
    def generate_connection_document(self, connection_id: str) -> bytes:
        """
        Generate connection security document.
        """
        connection = self.db.query(InternalSystemConnection).filter(
            InternalSystemConnection.id == connection_id,
            InternalSystemConnection.org_id == self.org_id
        ).first()
        
        if not connection:
            raise ValueError(f"Internal connection {connection_id} not found")
        
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
            'ConnTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'ConnHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'ConnBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # Title
        elements.append(Paragraph("INTERNAL SYSTEM CONNECTION", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Connection details
        elements.append(Paragraph("CONNECTION DETAILS", heading_style))
        elements.append(Paragraph(f"Connection Name: {connection.connection_name}", body_style))
        elements.append(Paragraph(f"Connection Number: {connection.connection_number}", body_style))
        elements.append(Paragraph(f"Connection Type: {connection.connection_type.upper()}", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Systems
        elements.append(Paragraph("SYSTEMS", heading_style))
        elements.append(Paragraph(f"Source System: {connection.source_system_name} ({connection.source_system_id})", body_style))
        elements.append(Paragraph(f"Target System: {connection.target_system_name} ({connection.target_system_id})", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Purpose
        elements.append(Paragraph("PURPOSE", heading_style))
        elements.append(Paragraph(connection.purpose, body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Data Types
        elements.append(Paragraph("DATA TYPES EXCHANGED", heading_style))
        if connection.data_types_exchanged:
            for data_type in connection.data_types_exchanged:
                elements.append(Paragraph(f"• {data_type}", body_style))
        else:
            elements.append(Paragraph("Data types to be specified.", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Security Requirements
        elements.append(Paragraph("SECURITY REQUIREMENTS", heading_style))
        if connection.security_requirements:
            for req in connection.security_requirements:
                elements.append(Paragraph(f"• {req}", body_style))
        else:
            elements.append(Paragraph("Security requirements to be specified.", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Security Controls
        elements.append(Paragraph("SECURITY CONTROLS", heading_style))
        if connection.security_controls:
            for control in connection.security_controls:
                elements.append(Paragraph(f"• {control}", body_style))
        else:
            elements.append(Paragraph("Security controls to be specified.", body_style))
        
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        
        logger.info(f"Generated connection document for {connection_id}")
        
        return pdf_bytes
    
    def _get_next_connection_number(self) -> str:
        """Get next sequential connection number"""
        today = datetime.now(timezone.utc).date()
        count = self.db.query(InternalSystemConnection).filter(
            InternalSystemConnection.org_id == self.org_id,
            func.date(InternalSystemConnection.created_at) == today
        ).count() or 0
        return f"{count + 1:03d}"
