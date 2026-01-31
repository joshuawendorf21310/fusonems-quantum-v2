"""
CA-6: Security Authorization Service

Tracks ATO and authorization status with reauthorization scheduling.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from core.logger import logger
from models.assessment import SecurityAuthorization, AuthorizationStatus, AuthorizationType


class AuthorizationService:
    """
    CA-6: Security Authorization Service
    
    Manages security authorizations and ATO tracking.
    """
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_authorization(
        self,
        system_id: str,
        system_name: str,
        authorization_type: str,
        authorization_boundary: Optional[str] = None,
        **kwargs
    ) -> SecurityAuthorization:
        """
        Create a new security authorization request.
        """
        authorization_number = f"ATO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._get_next_authorization_number()}"
        
        authorization = SecurityAuthorization(
            org_id=self.org_id,
            authorization_number=authorization_number,
            system_id=system_id,
            system_name=system_name,
            authorization_type=authorization_type,
            authorization_boundary=authorization_boundary,
            status=AuthorizationStatus.PENDING.value,
            created_by_user_id=self.user_id,
            **kwargs
        )
        
        self.db.add(authorization)
        self.db.commit()
        self.db.refresh(authorization)
        
        logger.info(f"Created authorization {authorization.id}: {authorization_number}")
        
        return authorization
    
    def grant_authorization(
        self,
        authorization_id: str,
        authorizing_official_name: str,
        authorizing_official_title: str,
        authorization_decision: str,
        authorization_expires_at: Optional[datetime] = None,
        authorization_conditions: Optional[List[str]] = None,
        **kwargs
    ) -> SecurityAuthorization:
        """
        Grant security authorization (ATO).
        """
        authorization = self.db.query(SecurityAuthorization).filter(
            SecurityAuthorization.id == authorization_id,
            SecurityAuthorization.org_id == self.org_id
        ).first()
        
        if not authorization:
            raise ValueError(f"Authorization {authorization_id} not found")
        
        authorization.status = AuthorizationStatus.AUTHORIZED.value
        authorization.authorizing_official_name = authorizing_official_name
        authorization.authorizing_official_title = authorizing_official_title
        authorization.authorization_decision = authorization_decision
        authorization.authorization_date = datetime.now(timezone.utc)
        authorization.authorized_by_user_id = self.user_id
        
        # Set expiration (default 3 years for initial, 1 year for reauthorization)
        if authorization_expires_at:
            authorization.authorization_expires_at = authorization_expires_at
        else:
            if authorization.authorization_type == AuthorizationType.INITIAL.value:
                authorization.authorization_expires_at = datetime.now(timezone.utc) + timedelta(days=1095)  # 3 years
            else:
                authorization.authorization_expires_at = datetime.now(timezone.utc) + timedelta(days=365)  # 1 year
        
        # Set next reauthorization due (typically 1 year before expiration)
        authorization.next_reauthorization_due = authorization.authorization_expires_at - timedelta(days=365)
        
        authorization.authorization_conditions = authorization_conditions or []
        
        self.db.commit()
        self.db.refresh(authorization)
        
        logger.info(f"Granted authorization {authorization_number} for system {authorization.system_name}")
        
        return authorization
    
    def generate_authorization_document(self, authorization_id: str) -> bytes:
        """
        Generate authorization document (ATO letter).
        """
        authorization = self.db.query(SecurityAuthorization).filter(
            SecurityAuthorization.id == authorization_id,
            SecurityAuthorization.org_id == self.org_id
        ).first()
        
        if not authorization:
            raise ValueError(f"Authorization {authorization_id} not found")
        
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
            'AuthTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'AuthHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'AuthBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # Title
        elements.append(Paragraph("AUTHORITY TO OPERATE (ATO)", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Authorization details
        elements.append(Paragraph(f"Authorization Number: {authorization.authorization_number}", body_style))
        elements.append(Paragraph(f"System: {authorization.system_name} ({authorization.system_id})", body_style))
        elements.append(Paragraph(f"Authorization Type: {authorization.authorization_type.upper()}", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Decision
        elements.append(Paragraph("AUTHORIZATION DECISION", heading_style))
        elements.append(Paragraph(authorization.authorization_decision or "Authorization decision pending.", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Authorization boundary
        if authorization.authorization_boundary:
            elements.append(Paragraph("AUTHORIZATION BOUNDARY", heading_style))
            elements.append(Paragraph(authorization.authorization_boundary, body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Dates
        elements.append(Paragraph("AUTHORIZATION DATES", heading_style))
        if authorization.authorization_date:
            elements.append(Paragraph(f"Authorization Date: {authorization.authorization_date.strftime('%Y-%m-%d')}", body_style))
        if authorization.authorization_expires_at:
            elements.append(Paragraph(f"Expiration Date: {authorization.authorization_expires_at.strftime('%Y-%m-%d')}", body_style))
        if authorization.next_reauthorization_due:
            elements.append(Paragraph(f"Next Reauthorization Due: {authorization.next_reauthorization_due.strftime('%Y-%m-%d')}", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Authorizing official
        if authorization.authorizing_official_name:
            elements.append(Paragraph("AUTHORIZING OFFICIAL", heading_style))
            elements.append(Paragraph(f"Name: {authorization.authorizing_official_name}", body_style))
            if authorization.authorizing_official_title:
                elements.append(Paragraph(f"Title: {authorization.authorizing_official_title}", body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Conditions
        if authorization.authorization_conditions:
            elements.append(Paragraph("AUTHORIZATION CONDITIONS", heading_style))
            for condition in authorization.authorization_conditions:
                elements.append(Paragraph(f"• {condition}", body_style))
        
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        
        logger.info(f"Generated authorization document for {authorization_id}")
        
        return pdf_bytes
    
    def check_reauthorization_due(self) -> List[SecurityAuthorization]:
        """
        Check for authorizations due for reauthorization.
        """
        now = datetime.now(timezone.utc)
        
        due_authorizations = self.db.query(SecurityAuthorization).filter(
            SecurityAuthorization.org_id == self.org_id,
            SecurityAuthorization.status == AuthorizationStatus.AUTHORIZED.value,
            SecurityAuthorization.next_reauthorization_due <= now
        ).all()
        
        return due_authorizations
    
    def _get_next_authorization_number(self) -> str:
        """Get next sequential authorization number"""
        today = datetime.now(timezone.utc).date()
        count = self.db.query(SecurityAuthorization).filter(
            SecurityAuthorization.org_id == self.org_id,
            func.date(SecurityAuthorization.created_at) == today
        ).count() or 0
        return f"{count + 1:03d}"
