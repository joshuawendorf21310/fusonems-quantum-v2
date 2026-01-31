"""
PL-4: Rules of Behavior Service

Generates rules of behavior documents and tracks user acknowledgments.
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
from models.planning import (
    RulesOfBehavior, RulesOfBehaviorAcknowledgment, RulesOfBehaviorVersion,
    RulesOfBehaviorStatus
)
from models.user import User


class RulesOfBehaviorService:
    """
    PL-4: Rules of Behavior Service
    
    Manages rules of behavior documents and user acknowledgments.
    """
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_rules(
        self,
        title: str,
        rules_content: str,
        version: str = "1.0",
        rules_sections: Optional[Dict] = None,
        **kwargs
    ) -> RulesOfBehavior:
        """
        Create new Rules of Behavior document.
        """
        rules = RulesOfBehavior(
            org_id=self.org_id,
            title=title,
            version=version,
            rules_content=rules_content,
            rules_sections=rules_sections or {},
            status=RulesOfBehaviorStatus.DRAFT.value,
            is_active=False,
            review_frequency_days=365,
            created_by_user_id=self.user_id,
            **kwargs
        )
        
        self.db.add(rules)
        self.db.commit()
        self.db.refresh(rules)
        
        logger.info(f"Created Rules of Behavior {rules.id}: {title}")
        
        return rules
    
    def generate_rules_document(self, rules_id: str) -> bytes:
        """
        Generate PDF document for Rules of Behavior.
        """
        rules = self.db.query(RulesOfBehavior).filter(
            RulesOfBehavior.id == rules_id,
            RulesOfBehavior.org_id == self.org_id
        ).first()
        
        if not rules:
            raise ValueError(f"Rules of Behavior {rules_id} not found")
        
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
            'RulesTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'RulesHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'RulesBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # Title
        elements.append(Paragraph(rules.title.upper(), title_style))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(f"Version: {rules.version}", body_style))
        elements.append(Paragraph(f"Effective Date: {rules.effective_date.strftime('%Y-%m-%d') if rules.effective_date else 'TBD'}", body_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Introduction
        elements.append(Paragraph("INTRODUCTION", heading_style))
        intro_text = (
            "These Rules of Behavior establish the expected conduct for all users "
            "of the information system. All users must read, understand, and acknowledge "
            "these rules before accessing the system."
        )
        elements.append(Paragraph(intro_text, body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Rules content
        if rules.rules_sections:
            # Structured sections
            for section_title, section_content in rules.rules_sections.items():
                elements.append(Paragraph(section_title.upper(), heading_style))
                if isinstance(section_content, list):
                    for item in section_content:
                        elements.append(Paragraph(f"• {item}", body_style))
                elif isinstance(section_content, str):
                    elements.append(Paragraph(section_content, body_style))
                elements.append(Spacer(1, 0.15*inch))
        else:
            # Plain text content
            elements.append(Paragraph("RULES OF BEHAVIOR", heading_style))
            # Split content into paragraphs
            paragraphs = rules.rules_content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    elements.append(Paragraph(para.strip(), body_style))
                    elements.append(Spacer(1, 0.1*inch))
        
        # Acknowledgment section
        elements.append(PageBreak())
        elements.append(Paragraph("ACKNOWLEDGMENT", heading_style))
        ack_text = (
            "By signing below, I acknowledge that I have read, understood, and agree to "
            "comply with the Rules of Behavior outlined in this document. I understand "
            "that violation of these rules may result in disciplinary action, including "
            "termination of access and potential legal consequences."
        )
        elements.append(Paragraph(ack_text, body_style))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("Signature: _________________________", body_style))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Name: _________________________", body_style))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Date: _________________________", body_style))
        
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        
        logger.info(f"Generated Rules of Behavior document for {rules_id}")
        
        return pdf_bytes
    
    def acknowledge_rules(
        self,
        rules_id: str,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RulesOfBehaviorAcknowledgment:
        """
        Record user acknowledgment of Rules of Behavior.
        """
        rules = self.db.query(RulesOfBehavior).filter(
            RulesOfBehavior.id == rules_id,
            RulesOfBehavior.org_id == self.org_id
        ).first()
        
        if not rules:
            raise ValueError(f"Rules of Behavior {rules_id} not found")
        
        # Check if already acknowledged this version
        existing = self.db.query(RulesOfBehaviorAcknowledgment).filter(
            RulesOfBehaviorAcknowledgment.rules_id == rules_id,
            RulesOfBehaviorAcknowledgment.user_id == user_id,
            RulesOfBehaviorAcknowledgment.rules_version == rules.version
        ).first()
        
        if existing:
            logger.warning(f"User {user_id} already acknowledged rules {rules_id} version {rules.version}")
            return existing
        
        acknowledgment = RulesOfBehaviorAcknowledgment(
            rules_id=rules_id,
            user_id=user_id,
            rules_version=rules.version,
            acknowledgment_ip_address=ip_address,
            acknowledgment_user_agent=user_agent,
            acknowledged_at=datetime.now(timezone.utc)
        )
        
        self.db.add(acknowledgment)
        self.db.commit()
        self.db.refresh(acknowledgment)
        
        logger.info(f"User {user_id} acknowledged Rules of Behavior {rules_id} version {rules.version}")
        
        return acknowledgment
    
    def get_acknowledgment_status(self, rules_id: str) -> Dict:
        """
        Get acknowledgment status for Rules of Behavior.
        """
        rules = self.db.query(RulesOfBehavior).filter(
            RulesOfBehavior.id == rules_id,
            RulesOfBehavior.org_id == self.org_id
        ).first()
        
        if not rules:
            raise ValueError(f"Rules of Behavior {rules_id} not found")
        
        # Get all users in organization
        from models.organization import Organization
        org = self.db.query(Organization).filter(Organization.id == self.org_id).first()
        
        total_users = self.db.query(User).filter(User.org_id == self.org_id).count()
        
        # Get acknowledgments for current version
        acknowledgments = self.db.query(RulesOfBehaviorAcknowledgment).filter(
            RulesOfBehaviorAcknowledgment.rules_id == rules_id,
            RulesOfBehaviorAcknowledgment.rules_version == rules.version
        ).count()
        
        return {
            "rules_id": str(rules.id),
            "rules_version": rules.version,
            "total_users": total_users,
            "acknowledged_count": acknowledgments,
            "acknowledgment_percentage": round((acknowledgments / total_users * 100) if total_users > 0 else 0, 2),
            "is_compliant": acknowledgments == total_users if total_users > 0 else False
        }
    
    def create_version(
        self,
        rules_id: str,
        version_number: str,
        change_summary: Optional[str] = None,
        changes_made: Optional[List[Dict]] = None
    ) -> RulesOfBehaviorVersion:
        """
        Create a new version of Rules of Behavior.
        """
        rules = self.db.query(RulesOfBehavior).filter(
            RulesOfBehavior.id == rules_id,
            RulesOfBehavior.org_id == self.org_id
        ).first()
        
        if not rules:
            raise ValueError(f"Rules of Behavior {rules_id} not found")
        
        version = RulesOfBehaviorVersion(
            rules_id=rules_id,
            version_number=version_number,
            change_summary=change_summary,
            changes_made=changes_made or [],
            created_by_user_id=self.user_id
        )
        
        self.db.add(version)
        
        # Update rules version
        rules.version = version_number
        rules.updated_at = datetime.now(timezone.utc)
        
        # Deactivate old version if active
        if rules.is_active:
            # Users will need to re-acknowledge new version
            pass
        
        self.db.commit()
        self.db.refresh(version)
        
        logger.info(f"Created version {version_number} for Rules of Behavior {rules_id}")
        
        return version
    
    def activate_rules(self, rules_id: str) -> RulesOfBehavior:
        """
        Activate Rules of Behavior (requires approval).
        """
        rules = self.db.query(RulesOfBehavior).filter(
            RulesOfBehavior.id == rules_id,
            RulesOfBehavior.org_id == self.org_id
        ).first()
        
        if not rules:
            raise ValueError(f"Rules of Behavior {rules_id} not found")
        
        rules.status = RulesOfBehaviorStatus.ACTIVE.value
        rules.is_active = True
        rules.effective_date = datetime.now(timezone.utc)
        
        if not rules.next_review_date:
            rules.next_review_date = datetime.now(timezone.utc) + timedelta(days=rules.review_frequency_days)
        
        self.db.commit()
        self.db.refresh(rules)
        
        logger.info(f"Activated Rules of Behavior {rules_id}")
        
        return rules
