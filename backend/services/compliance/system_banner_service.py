"""
System Use Notification Service for FedRAMP AC-8 Compliance

FedRAMP AC-8 requires:
- Notify users of monitoring
- State authorized use only
- Display before granting access
- Retain consent records
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from models.banner_acceptance import BannerAcceptance
from core.logger import logger


class SystemBannerService:
    """
    Service for managing system use notification banner (FedRAMP AC-8).
    
    Provides FedRAMP-compliant banner text and tracks user acceptance.
    """
    
    # Current banner version - increment when banner text changes
    CURRENT_BANNER_VERSION = "1.0"
    
    # Standard FedRAMP-compliant system use notification text
    STANDARD_BANNER_TEXT = (
        "You are accessing a U.S. Government information system. "
        "This system is for the use of authorized users only. "
        "Individuals using this computer system without authority, or in excess of their authority, "
        "are subject to having all of their activities on this system monitored and recorded by "
        "system personnel. In the course of monitoring individuals improperly using this system, "
        "or in the course of system maintenance, the activities of authorized users may also be monitored. "
        "Anyone using this system expressly consents to such monitoring and is advised that if such "
        "monitoring reveals possible evidence of criminal activity, system personnel may provide the "
        "evidence of such monitoring to law enforcement officials."
    )
    
    @classmethod
    def get_banner(cls) -> dict:
        """
        Get the current system use notification banner.
        
        Returns:
            dict with banner text and version
        """
        return {
            "text": cls.STANDARD_BANNER_TEXT,
            "version": cls.CURRENT_BANNER_VERSION,
            "requires_acceptance": True,
        }
    
    @classmethod
    def has_user_accepted_banner(
        cls,
        db: Session,
        user_id: int,
        banner_version: Optional[str] = None
    ) -> bool:
        """
        Check if user has accepted the current banner version.
        
        Args:
            db: Database session
            user_id: User ID to check
            banner_version: Banner version to check (defaults to current version)
            
        Returns:
            True if user has accepted the banner, False otherwise
        """
        if banner_version is None:
            banner_version = cls.CURRENT_BANNER_VERSION
        
        acceptance = db.query(BannerAcceptance).filter(
            BannerAcceptance.user_id == user_id,
            BannerAcceptance.banner_version == banner_version
        ).first()
        
        return acceptance is not None
    
    @classmethod
    def record_banner_acceptance(
        cls,
        db: Session,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        banner_version: Optional[str] = None
    ) -> BannerAcceptance:
        """
        Record user acceptance of the system use notification banner.
        
        Args:
            db: Database session
            user_id: User ID accepting the banner
            ip_address: IP address of the user
            user_agent: User agent string
            banner_version: Banner version being accepted (defaults to current version)
            
        Returns:
            BannerAcceptance record
        """
        if banner_version is None:
            banner_version = cls.CURRENT_BANNER_VERSION
        
        # Check if user already accepted this version
        existing = db.query(BannerAcceptance).filter(
            BannerAcceptance.user_id == user_id,
            BannerAcceptance.banner_version == banner_version
        ).first()
        
        if existing:
            logger.info(
                "User %d already accepted banner version %s",
                user_id,
                banner_version
            )
            return existing
        
        # Create new acceptance record
        acceptance = BannerAcceptance(
            user_id=user_id,
            banner_version=banner_version,
            ip_address=ip_address,
            user_agent=user_agent,
            accepted_at=datetime.now(timezone.utc),
        )
        
        db.add(acceptance)
        db.commit()
        db.refresh(acceptance)
        
        logger.info(
            "User %d accepted banner version %s from IP %s",
            user_id,
            banner_version,
            ip_address or "unknown"
        )
        
        return acceptance
    
    @classmethod
    def require_banner_acceptance(
        cls,
        db: Session,
        user_id: int
    ) -> bool:
        """
        Check if banner acceptance is required for the user.
        This enforces that users must accept the banner before accessing the system.
        
        Args:
            db: Database session
            user_id: User ID to check
            
        Returns:
            True if acceptance is required, False if already accepted
        """
        return not cls.has_user_accepted_banner(db, user_id)
