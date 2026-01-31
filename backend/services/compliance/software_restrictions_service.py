"""
Software Usage Restrictions Service for FedRAMP CM-10 Compliance

FedRAMP Requirement CM-10: Software Usage Restrictions
- License tracking
- Usage monitoring
- Compliance enforcement
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.cm_controls import SoftwareLicense


class SoftwareRestrictionsService:
    """
    Service for software usage restrictions (CM-10).
    """
    
    @staticmethod
    def register_license(
        db: Session,
        org_id: int,
        software_name: str,
        license_type: str,
        software_version: Optional[str] = None,
        vendor: Optional[str] = None,
        license_key: Optional[str] = None,
        license_agreement: Optional[str] = None,
        max_installations: Optional[int] = None,
        usage_restrictions: Optional[Dict] = None,
        issued_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ) -> SoftwareLicense:
        """
        Register a software license.
        
        Args:
            db: Database session
            org_id: Organization ID
            software_name: Name of software
            license_type: Type of license
            software_version: Software version
            vendor: Vendor name
            license_key: License key (should be encrypted)
            license_agreement: License agreement text
            max_installations: Maximum allowed installations
            usage_restrictions: Usage restrictions
            issued_at: License issue date
            expires_at: License expiration date
            
        Returns:
            Created SoftwareLicense
        """
        # Check if license already exists
        existing = db.query(SoftwareLicense).filter(
            SoftwareLicense.software_name == software_name,
            SoftwareLicense.org_id == org_id,
            SoftwareLicense.software_version == software_version,
        ).first()
        
        if existing:
            # Update existing
            existing.license_type = license_type
            existing.vendor = vendor
            existing.license_key = license_key
            existing.license_agreement = license_agreement
            existing.max_installations = max_installations
            existing.usage_restrictions = usage_restrictions
            existing.issued_at = issued_at
            existing.expires_at = expires_at
            existing.last_checked_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing
        
        license = SoftwareLicense(
            org_id=org_id,
            software_name=software_name,
            software_version=software_version,
            vendor=vendor,
            license_type=license_type,
            license_key=license_key,  # Should be encrypted in production
            license_agreement=license_agreement,
            max_installations=max_installations,
            current_installations=0,
            usage_restrictions=usage_restrictions,
            license_status="active",
            is_compliant=True,
            issued_at=issued_at,
            expires_at=expires_at,
            last_checked_at=datetime.now(timezone.utc),
        )
        
        db.add(license)
        db.commit()
        db.refresh(license)
        
        logger.info(f"Software license registered: {software_name} (org_id={org_id})")
        
        return license
    
    @staticmethod
    def record_installation(
        db: Session,
        license_id: str,
        org_id: int,
    ) -> SoftwareLicense:
        """Record a software installation"""
        license = db.query(SoftwareLicense).filter(
            SoftwareLicense.id == license_id,
            SoftwareLicense.org_id == org_id,
        ).first()
        
        if not license:
            raise ValueError(f"License {license_id} not found")
        
        # Check if installation is allowed
        if license.max_installations and license.current_installations >= license.max_installations:
            license.is_compliant = False
            db.commit()
            raise ValueError(f"Maximum installations ({license.max_installations}) exceeded")
        
        license.current_installations += 1
        license.last_checked_at = datetime.now(timezone.utc)
        
        # Check compliance
        if license.max_installations:
            license.is_compliant = license.current_installations <= license.max_installations
        
        db.commit()
        db.refresh(license)
        
        logger.info(f"Installation recorded: {license.software_name} (count={license.current_installations})")
        
        return license
    
    @staticmethod
    def record_uninstallation(
        db: Session,
        license_id: str,
        org_id: int,
    ) -> SoftwareLicense:
        """Record a software uninstallation"""
        license = db.query(SoftwareLicense).filter(
            SoftwareLicense.id == license_id,
            SoftwareLicense.org_id == org_id,
        ).first()
        
        if not license:
            raise ValueError(f"License {license_id} not found")
        
        if license.current_installations > 0:
            license.current_installations -= 1
        
        license.last_checked_at = datetime.now(timezone.utc)
        
        # Check compliance
        if license.max_installations:
            license.is_compliant = license.current_installations <= license.max_installations
        
        db.commit()
        db.refresh(license)
        
        return license
    
    @staticmethod
    def check_compliance(
        db: Session,
        org_id: int,
    ) -> List[SoftwareLicense]:
        """Check license compliance and return non-compliant licenses"""
        licenses = db.query(SoftwareLicense).filter(
            SoftwareLicense.org_id == org_id,
            SoftwareLicense.license_status == "active",
        ).all()
        
        non_compliant = []
        now = datetime.now(timezone.utc)
        
        for license in licenses:
            # Check expiration
            if license.expires_at and license.expires_at < now:
                license.license_status = "expired"
                license.is_compliant = False
                non_compliant.append(license)
                continue
            
            # Check installation limits
            if license.max_installations and license.current_installations > license.max_installations:
                license.is_compliant = False
                non_compliant.append(license)
                continue
            
            # Mark as compliant if checks pass
            license.is_compliant = True
            license.last_checked_at = now
        
        if non_compliant:
            db.commit()
            logger.warning(f"Found {len(non_compliant)} non-compliant licenses")
        
        return non_compliant
    
    @staticmethod
    def get_licenses(
        db: Session,
        org_id: int,
        compliant_only: bool = False,
    ) -> List[SoftwareLicense]:
        """Get software licenses"""
        query = db.query(SoftwareLicense).filter(
            SoftwareLicense.org_id == org_id
        )
        
        if compliant_only:
            query = query.filter(SoftwareLicense.is_compliant == True)
        
        return query.order_by(desc(SoftwareLicense.last_checked_at)).all()
