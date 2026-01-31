"""
Spam Protection Service for FedRAMP SI-8 Compliance

This service provides:
- Email filtering
- Content scanning

FedRAMP SI-8: Spam Protection
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from email.utils import parseaddr

from sqlalchemy.orm import Session

from models.system_integrity import (
    SpamFilterResult,
    SpamClassification,
)
from utils.logger import logger


class SpamProtectionService:
    """
    Service for spam protection and email filtering.
    
    FedRAMP SI-8: Spam Protection
    """
    
    # Common spam keywords
    SPAM_KEYWORDS = [
        "free", "click here", "limited time", "act now", "urgent",
        "winner", "congratulations", "prize", "claim", "guaranteed",
        "no risk", "special offer", "exclusive", "deal", "discount",
    ]
    
    # Phishing indicators
    PHISHING_INDICATORS = [
        "verify your account", "suspended", "verify now", "click to verify",
        "account locked", "security alert", "unauthorized access",
        "update your information", "confirm your identity",
    ]
    
    def __init__(self, db: Session):
        """
        Initialize spam protection service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def filter_email(
        self,
        message_id: str,
        subject: str,
        sender_email: str,
        recipient_email: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> SpamFilterResult:
        """
        Filter an email for spam and threats.
        
        Args:
            message_id: Unique message identifier
            subject: Email subject
            sender_email: Sender email address
            recipient_email: Recipient email address
            body_text: Plain text body
            body_html: HTML body
            user_id: User ID
            organization_id: Organization ID
            
        Returns:
            SpamFilterResult record
        """
        # Combine text for analysis
        full_text = f"{subject} {body_text or ''} {body_html or ''}".lower()
        
        # Calculate spam score
        spam_score = self._calculate_spam_score(subject, full_text, sender_email)
        
        # Classify email
        classification, confidence = self._classify_email(
            spam_score, subject, full_text, sender_email
        )
        
        # Check for phishing
        phishing_detected = self._detect_phishing(subject, full_text)
        
        # Check for malware indicators
        malware_detected = self._detect_malware_indicators(full_text)
        
        # Determine action
        action = self._determine_action(classification, spam_score, phishing_detected, malware_detected)
        
        # Create filter result
        result = SpamFilterResult(
            message_id=message_id,
            message_subject=subject,
            sender_email=sender_email,
            recipient_email=recipient_email,
            classification=classification.value,
            spam_score=spam_score,
            confidence=confidence,
            filter_engine="custom",
            phishing_detected=phishing_detected,
            malware_detected=malware_detected,
            content_scanned=True,
            action_taken=action,
            action_taken_at=datetime.utcnow() if action != "delivered" else None,
            user_id=user_id,
            organization_id=organization_id,
        )
        
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        
        logger.info(
            f"Email filtered: {message_id}",
            extra={
                "message_id": message_id,
                "classification": classification.value,
                "spam_score": spam_score,
                "phishing_detected": phishing_detected,
                "event_type": "spam.email.filtered",
            }
        )
        
        return result
    
    def get_spam_statistics(
        self,
        days: int = 30,
    ) -> Dict:
        """
        Get spam filtering statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        total = self.db.query(SpamFilterResult).filter(
            SpamFilterResult.created_at >= since
        ).count()
        
        spam_count = self.db.query(SpamFilterResult).filter(
            SpamFilterResult.created_at >= since,
            SpamFilterResult.classification == SpamClassification.SPAM.value,
        ).count()
        
        phishing_count = self.db.query(SpamFilterResult).filter(
            SpamFilterResult.created_at >= since,
            SpamFilterResult.phishing_detected == True,
        ).count()
        
        malware_count = self.db.query(SpamFilterResult).filter(
            SpamFilterResult.created_at >= since,
            SpamFilterResult.malware_detected == True,
        ).count()
        
        return {
            "total_emails": total,
            "spam_count": spam_count,
            "phishing_count": phishing_count,
            "malware_count": malware_count,
            "spam_rate": (spam_count / total * 100) if total > 0 else 0.0,
            "period_days": days,
        }
    
    def _calculate_spam_score(
        self,
        subject: str,
        full_text: str,
        sender_email: str,
    ) -> int:
        """
        Calculate spam score (0-100).
        
        Args:
            subject: Email subject
            full_text: Full email text
            sender_email: Sender email address
            
        Returns:
            Spam score (0-100)
        """
        score = 0
        
        # Check for spam keywords
        for keyword in self.SPAM_KEYWORDS:
            if keyword in full_text:
                score += 5
        
        # Check subject for spam indicators
        subject_lower = subject.lower()
        if any(keyword in subject_lower for keyword in ["!!!", "$$$", "FREE", "CLICK"]):
            score += 10
        
        # Check sender email
        if self._is_suspicious_sender(sender_email):
            score += 15
        
        # Check for excessive capitalization
        if len(subject) > 0:
            caps_ratio = sum(1 for c in subject if c.isupper()) / len(subject)
            if caps_ratio > 0.5:
                score += 10
        
        # Check for suspicious links
        link_count = len(re.findall(r'http[s]?://', full_text))
        if link_count > 5:
            score += 10
        
        return min(score, 100)
    
    def _classify_email(
        self,
        spam_score: int,
        subject: str,
        full_text: str,
        sender_email: str,
    ) -> tuple[SpamClassification, float]:
        """
        Classify email based on spam score and indicators.
        
        Args:
            spam_score: Calculated spam score
            subject: Email subject
            full_text: Full email text
            sender_email: Sender email address
            
        Returns:
            Tuple of (classification, confidence)
        """
        # Check for phishing first
        if self._detect_phishing(subject, full_text):
            return SpamClassification.PHISHING, 0.9
        
        # Check for malware
        if self._detect_malware_indicators(full_text):
            return SpamClassification.MALWARE, 0.85
        
        # Classify based on spam score
        if spam_score >= 70:
            return SpamClassification.SPAM, spam_score / 100.0
        elif spam_score >= 40:
            return SpamClassification.SUSPICIOUS, spam_score / 100.0
        else:
            return SpamClassification.HAM, 1.0 - (spam_score / 100.0)
    
    def _detect_phishing(self, subject: str, full_text: str) -> bool:
        """
        Detect phishing indicators.
        
        Args:
            subject: Email subject
            full_text: Full email text
            
        Returns:
            True if phishing detected
        """
        text_lower = full_text.lower()
        subject_lower = subject.lower()
        
        # Check for phishing indicators
        for indicator in self.PHISHING_INDICATORS:
            if indicator in text_lower or indicator in subject_lower:
                return True
        
        # Check for suspicious URLs
        urls = re.findall(r'http[s]?://[^\s<>"{}|\\^`\[\]]+', full_text)
        for url in urls:
            # Check for URL shorteners
            if any(domain in url for domain in ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co']):
                return True
            
            # Check for mismatched domains
            if 'verify' in text_lower or 'update' in text_lower:
                return True
        
        return False
    
    def _detect_malware_indicators(self, full_text: str) -> bool:
        """
        Detect malware indicators in email.
        
        Args:
            full_text: Full email text
            
        Returns:
            True if malware indicators detected
        """
        text_lower = full_text.lower()
        
        # Check for executable file mentions
        executable_extensions = ['.exe', '.bat', '.cmd', '.scr', '.vbs', '.js']
        for ext in executable_extensions:
            if ext in text_lower:
                return True
        
        # Check for suspicious phrases
        malware_phrases = [
            "download now", "install software", "run this file",
            "enable macros", "click to install",
        ]
        
        for phrase in malware_phrases:
            if phrase in text_lower:
                return True
        
        return False
    
    def _is_suspicious_sender(self, sender_email: str) -> bool:
        """
        Check if sender email is suspicious.
        
        Args:
            sender_email: Sender email address
            
        Returns:
            True if suspicious
        """
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\d{10,}@',  # Many digits
            r'[a-z]{1,2}\d{6,}@',  # Few letters, many digits
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, sender_email.lower()):
                return True
        
        return False
    
    def _determine_action(
        self,
        classification: SpamClassification,
        spam_score: int,
        phishing_detected: bool,
        malware_detected: bool,
    ) -> str:
        """
        Determine action to take based on classification.
        
        Args:
            classification: Email classification
            spam_score: Spam score
            phishing_detected: Whether phishing detected
            malware_detected: Whether malware detected
            
        Returns:
            Action to take
        """
        if malware_detected or phishing_detected:
            return "quarantine"
        elif classification == SpamClassification.SPAM:
            return "quarantine"
        elif classification == SpamClassification.SUSPICIOUS:
            return "flag"
        else:
            return "delivered"
