"""
Founder Email Service - SMTP/IMAP (Mailu/self-hosted).

Provides: Founder dashboard email management, send/receive via SMTP/IMAP,
email tracking, AI-assisted composition, founder-focused analytics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_

from core.config import settings
from models.email import EmailThread, EmailMessage, EmailLabel
from models.user import User
from models.organization import Organization
from utils.logger import logger
from utils.write_ops import audit_and_event
from services.ai import get_ai_assist_config
from services.email.email_transport_service import send_smtp_email_simple


class FounderEmailService:
    """Complete email service for founder communications"""
    
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
        self.from_address = None  # Set per org
        self.server_info = None
        
        # Initialize org-specific settings
        self._initialize_org_settings()
    
    def _initialize_org_settings(self):
        org = self.db.query(Organization).get(self.org_id)
        if org and hasattr(org, 'email_settings') and org.email_settings:
            self.from_address = org.email_settings.get('from_address')
            self.server_info = org.email_settings.get('server_info')
        if not self.from_address:
            self.from_address = getattr(settings, "FOUNDER_EMAIL", None) or settings.SMTP_USERNAME or settings.SMTP_FROM_EMAIL or (settings.SMTP_HOST and f"noreply@{settings.SMTP_HOST}") or "noreply@local"
    
    # FOUNDER DASHBOARD FUNCTIONS
    
    def get_founder_email_stats(self) -> Dict[str, Any]:
        """Get email statistics for founder dashboard"""
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Unread emails
        unread_count = self.db.query(EmailMessage).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.direction == 'inbound',
            EmailMessage.status == 'delivered',
            EmailMessage.meta.get('read') == False
        ).count()
        
        # Messages waiting response
        waiting_response = self.db.query(EmailMessage).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.direction == 'inbound',
            EmailMessage.created_at >= twenty_four_hours_ago,
            EmailMessage.meta.get('needs_response') == True
        ).count()
        
        # Failed deliveries in last 24h
        failed_count = self.db.query(EmailMessage).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.created_at >= twenty_four_hours_ago,
            or_(
                EmailMessage.status == 'failed',
                EmailMessage.status == 'bounce'
            )
        ).count()
        
        # Recent activity last 7 days
        recent_count = self.db.query(EmailMessage).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.created_at >= one_week_ago
        ).count()
        
        # Response time average
        response_avg = self.db.query(func.avg(
            func.extract('EPOCH', EmailMessage.meta.get('responded_at')) - 
            func.extract('EPOCH', EmailMessage.created_at)
        )).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.direction == 'inbound',
            EmailMessage.meta.get('responded_at').isnot(None)
        ).scalar()
        
        return {
            'unread_messages': unread_count,
            'messages_needing_response': waiting_response,
            'failed_deliveries_24h': failed_count,
            'recent_activity_7d': recent_count,
            'avg_response_minutes': round(response_avg / 60) if response_avg else 0,
            'sender_status': 'active' if self.from_address else 'needs_setup'
        }
    
    def get_recent_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent emails for founder dashboard"""
        emails = self.db.query(EmailMessage).filter(
            EmailMessage.org_id == self.org_id
        ).order_by(EmailMessage.created_at.desc()).limit(limit).all()
        
        return [
            {
                'id': email.id,
                'direction': email.direction,
                'sender': email.sender,
                'recipients': email.recipients,
                'subject': email.subject,
                'body_preview': email.body_plain[:200] if email.body_plain else '',
                'status': email.status,
                'created_at': email.created_at.isoformat(),
                'is_read': email.meta.get('read', False),
                'needs_response': email.meta.get('needs_response', False),
                'message_id': email.postmark_message_id
            }
            for email in emails
        ]
    
    def get_inbound_emails_needing_response(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get inbound emails that need founder response"""
        emails = self.db.query(EmailMessage).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.direction == 'inbound',
            EmailMessage.meta.get('needs_response') == True
        ).order_by(EmailMessage.created_at.desc()).limit(limit).all()
        
        return [
            {
                'id': email.id,
                'from_address': email.sender,
                'subject': email.subject,
                'body_preview': email.body_plain[:300] if email.body_plain else '',
                'created_at': email.created_at.isoformat(),
                'urgency': self._calculate_urgency(email),
                'labels': self._get_email_labels(email.id)
            }
            for email in emails
        ]
    
    def _calculate_urgency(self, email: EmailMessage) -> str:
        """Calculate email urgency for founder attention"""
        if email.meta.get('sender_in_org'):
            return "high"
        
        sender_domains = ['patient', 'arnp', 'doctor']
        if any(domain in email.sender.lower() for domain in sender_domains):
            return "high"
        
        if email.meta.get('keywords_in_subject'):
            urgent_keywords = ['urgent', 'emergency', 'asap', 'critical']
            if any(keyword in email.subject.lower() for keyword in urgent_keywords):
                return "high"
        
        # Based on time
        if email.created_at < datetime.utcnow() - timedelta(hours=24):
            return "high"
        elif email.created_at < datetime.utcnow() - timedelta(hours=6):
            return "medium"
        
        return "normal"
    
    def _get_email_labels(self, message_id: int) -> List[str]:
        """Get labels for email message"""
        labels = []
        for label_link in self.db.query(EmailMessageLabel).filter(
            EmailMessageLabel.message_id == message_id
        ).all():
            label = self.db.query(EmailLabel).get(label_link.label_id)
            if label:
                labels.append(label.name)
        return labels
    
    # EMAIL SENDING FUNCTIONS
    
    def send_email(
        self, 
        sender: User,
        to_email: str,
        subject: str,
        body_text: str = "",
        body_html: str = "",
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[Dict[str, Any]] = None,
        reply_to: str = None,
        template_name: str = None,
        urgent: bool = False,
        request: Any = None
    ) -> Dict[str, Any]:
        """Send email as founder"""
        
        if not self.from_address:
            raise RuntimeError("Email not configured for this organization (set org email_settings.from_address or SMTP_USERNAME)")

        thread = self._get_or_create_thread(sender, to_email, subject)
        email_message = EmailMessage(
            org_id=self.org_id,
            thread_id=thread.id,
            classification="founder_comm",
            direction='outbound',
            status='queued',
            sender=self.from_address,
            recipients=[to_email] + (cc_emails or []) + (bcc_emails or []),
            cc=cc_emails or [],
            bcc=bcc_emails or [],
            subject=subject,
            body_plain=body_text,
            body_html=body_html,
            created_by=sender.id,
            meta={
                'urgent': urgent,
                'sender_user_id': sender.id,
                'template': template_name
            }
        )
        if request:
            apply_training_mode(email_message, request)
        self.db.add(email_message)
        self.db.commit()
        self.db.refresh(email_message)

        try:
            send_smtp_email_simple(
                to=to_email,
                subject=subject,
                html_body=body_html or body_text,
                from_addr=self.from_address,
                text_body=body_text or None,
                cc=cc_emails,
                bcc=bcc_emails,
                reply_to=reply_to,
            )
            email_message.status = 'delivered'
            email_message.postmark_message_id = ''
            email_message.postmark_record_type = 'Outbound'
            email_message.meta['transport'] = 'smtp'
            if request:
                audit_and_event(
                    db=self.db,
                    request=request,
                    user=sender,
                    action='send',
                    resource='email_message',
                    classification=email_message.classification,
                    after_state={'message_id': email_message.id, 'to': to_email},
                    event_type='email.sent',
                    event_payload={
                        'to': to_email,
                        'subject': subject,
                        'urgent': urgent
                    }
                )
            logger.info(f"Email sent from founder: {email_message.id} -> {to_email}")
            return {
                'success': True,
                'message_id': email_message.id,
                'postmark_id': '',
                'thread_id': thread.id
            }
        except Exception as e:
            email_message.status = 'failed'
            email_message.error_message = str(e)
            self.db.commit()
            logger.error(f"Failed to send email: {e}")
            raise RuntimeError(f"Email send failed: {str(e)}")
    
    def _get_or_create_thread(self, sender: User, to_email: str, subject: str) -> EmailThread:
        """Get existing thread or create new one"""
        # Normalize subject
        normalized_subject = subject.lower().strip()
        
        # Look for existing thread
        thread = self.db.query(EmailThread).filter(
            EmailThread.org_id == self.org_id,
            EmailThread.normalized_subject == normalized_subject,
            EmailThread.created_by == sender.id
        ).first()
        
        if not thread:
            thread = EmailThread(
                org_id=self.org_id,
                subject=subject,
                normalized_subject=normalized_subject,
                status='open',
                created_by=sender.id
            )
            self.db.add(thread)
            self.db.commit()
            self.db.refresh(thread)
        
        return thread
    
    # AI EMAIL ASSISTANT FUNCTIONS
    
    def generate_email_draft(
        self,
        sender: User,
        recipient_email: str,
        subject_context: str,
        context: str,
        tone: str = "professional",
        length: str = "medium",
        request: Any = None
    ) -> Dict[str, Any]:
        """AI generate email draft for founder"""
        
        ai_config = get_ai_assist_config(self.org_id)
        
        prompt = f"""
Generate a {tone} email for a founder/founder-administrator. 

Context: {context}
Recipient: {recipient_email}
Subject Context: {subject_context}
Tone: {tone}
Length: {length}

Guidelines:
- Be concise but comprehensive\n- Include next steps or calls to action where appropriate\n- Use professional language appropriate to EMS/founder communications\n- Include contact information signature\n- Address any billing/payment/facility context appropriately

Output format: JSON with \"subject\" and \"body_text\" fields
"""
        
        # Call AI service (Ollama)
        ai_response = self._call_ollama_for_email(prompt, tone=tone)
        
        return {
            'success': True,
            'subject': ai_response.get('subject', ''),
            'body_text': ai_response.get('body_text', ''),
            'recipients': [recipient_email],
            'generated_by_ai': True,
            'confidence': ai_response.get('confidence', 0.8)
        }
    
    def _call_ollama_for_email(self, prompt: str, tone: str = "professional") -> Dict[str, Any]:
        """Call AI (Ollama) for email generation"""
        
        from services.ai import get_ai_client
        
        client = get_ai_client()
        response = client.generate(
            prompt=prompt,
            model="neural-chat",  # Or founder-specific model
            temperature=0.7,
            max_tokens=1000
        )
        
        if not response.get('success'):
            return {
                'subject': 'Generated Email',
                'body_text': 'AI generation failed. Please draft manually.',
                'confidence': 0.0
            }
        
        return {
            'subject': response.get('response', {}).get('subject', ''),
            'body_text': response.get('response', {}).get('body_text', ''),
            'confidence': response.get('confidence', 0.8)
        }
    
    def suggest_email_content(
        self,
        recipient_email: str,
        subject_line: str,
        context: str,
        tone: str = "professional"
    ) -> List[str]:
        """AI suggest email content improvements for founder"""
        
        prompt = f"""
Review this email content for a founder and suggest improvements:\n\nRecipient: {recipient_email}\nSubject: {subject_line}\n\nContext: {context}\nTone: {tone}\n\nSuggestions needed for:\n1. Subject line optimization\n2. Opening sentence hook\n3. Call to action strength\n4. Tone appropriateness\n5. Missing key information\n\nFormat: 5 bullet points with specific suggestions\n"""
        
        ai_response = self._call_ollama_for_email(prompt)
        suggestions = ai_response.get('body_text', '').split('\n')
        return [s.strip() for s in suggestions if s.strip()][:5]
    
    # COMMUNICATIONS TRACKING
    
    def track_communication_outreach(self, recipient_email: str) -> Dict[str, Any]:
        """Track founder communication effectiveness"""
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Count communications to this email
        communication_count = self.db.query(func.count(EmailMessage.id)).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.recipients.like(f'%{recipient_email}%'),
            EmailMessage.created_at >= thirty_days_ago
        ).scalar()
        
        # Count responses
        response_count = self.db.query(func.count(EmailMessage.id)).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.direction == 'inbound',
            EmailMessage.sender == recipient_email,
            EmailMessage.created_at >= thirty_days_ago
        ).scalar()
        
        # Calculate average response time
        response_time = self.db.query(func.avg(
            func.extract('EPOCH', EmailMessage.meta.get('responded_at')) - 
            func.extract('EPOCH', EmailMessage.created_at)
        )).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.direction == 'inbound',
            EmailMessage.sender == recipient_email,
            EmailMessage.created_at >= thirty_days_ago,
            EmailMessage.meta.get('responded_at').isnot(None)
        ).scalar()
        
        # Figure out relationship score
        if communication_count > 10 and response_count > 5:
            status = "responsive"
        elif communication_count > 5 and response_count > 2:
            status = "moderately_responsive"
        else:
            status = "needs_followup"
        
        return {
            'recipient': recipient_email,
            'communication_count_30d': communication_count or 0,
            'response_count_30d': response_count or 0,
            'response_rate': (response_count / communication_count * 100) if communication_count > 0 else 0,
            'avg_response_hours': round(response_time / 3600) if response_time else 0,
            'relationship_status': status,
            'last_contact': self._get_last_contact(recipient_email)
        }
    
    def _get_last_contact(self, recipient_email: str) -> Optional[datetime]:
        """Get most recent contact timestamp"""
        last_message = self.db.query(EmailMessage).filter(
            EmailMessage.org_id == self.org_id,
            EmailMessage.recipients.like(f'%{recipient_email}%')
        ).order_by(EmailMessage.created_at.desc()).first()
        
        return last_message.created_at if last_message else None