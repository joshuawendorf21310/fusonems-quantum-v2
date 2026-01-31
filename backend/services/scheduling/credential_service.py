from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from models.user import User

logger = logging.getLogger(__name__)


class CredentialValidationService:
    CERTIFICATION_MAPPING = {
        "paramedic": ["Paramedic", "NRP", "National Registry Paramedic", "P"],
        "emt": ["EMT", "EMT-B", "EMT-Basic", "National Registry EMT", "NREMT"],
        "aemt": ["AEMT", "EMT-Advanced", "Advanced EMT"],
        "nurse": ["RN", "LPN", "Registered Nurse", "Licensed Practical Nurse"],
        "acls": ["ACLS", "Advanced Cardiac Life Support"],
        "pals": ["PALS", "Pediatric Advanced Life Support"],
        "bls": ["BLS", "Basic Life Support", "CPR"],
        "itls": ["ITLS", "International Trauma Life Support"],
        "phtls": ["PHTLS", "Prehospital Trauma Life Support"],
        "als": ["ALS", "Advanced Life Support"],
        "pilot": ["ATP", "Commercial Pilot", "Pilot Certificate"],
        "driver": ["Ambulance Driver", "Emergency Vehicle Operator", "EVOC", "CDL"],
    }

    @staticmethod
    def normalize_certification_type(cert_type: str) -> str:
        cert_lower = cert_type.lower().strip()
        for category, variations in CredentialValidationService.CERTIFICATION_MAPPING.items():
            if cert_lower in [v.lower() for v in variations] or cert_lower == category:
                return category
        return cert_lower

    @staticmethod
    def check_user_certifications(
        db: Session,
        user_id: int,
        required_certifications: List[str],
        check_date: Optional[date] = None,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        from models.hr_personnel import Certification, CertificationStatus, Personnel
        
        if not required_certifications:
            return True, []
        
        target_date = check_date or date.today()
        
        personnel = db.query(Personnel).filter(
            or_(
                Personnel.email == db.query(User.email).filter(User.id == user_id).scalar_subquery(),
                Personnel.id == user_id
            )
        ).first()
        
        if not personnel:
            logger.warning(f"No personnel record found for user {user_id}")
            return False, [{
                "certification": "all",
                "status": "missing",
                "message": "No personnel record found in HR system",
            }]
        
        user_certs = db.query(Certification).filter(
            and_(
                Certification.personnel_id == personnel.id,
                Certification.status.in_([CertificationStatus.ACTIVE, CertificationStatus.EXPIRING_SOON])
            )
        ).all()
        
        user_cert_types = {}
        for cert in user_certs:
            normalized = CredentialValidationService.normalize_certification_type(cert.certification_type)
            if normalized not in user_cert_types or cert.expiration_date > user_cert_types[normalized].expiration_date:
                user_cert_types[normalized] = cert
        
        validation_results = []
        all_valid = True
        
        for required in required_certifications:
            required_normalized = CredentialValidationService.normalize_certification_type(required)
            
            if required_normalized in user_cert_types:
                cert = user_cert_types[required_normalized]
                
                if cert.expiration_date < target_date:
                    all_valid = False
                    validation_results.append({
                        "certification": required,
                        "status": "expired",
                        "expiration_date": cert.expiration_date.isoformat(),
                        "message": f"{required} certification expired on {cert.expiration_date}",
                    })
                elif cert.expiration_date < target_date + timedelta(days=30):
                    validation_results.append({
                        "certification": required,
                        "status": "expiring_soon",
                        "expiration_date": cert.expiration_date.isoformat(),
                        "message": f"{required} certification expires on {cert.expiration_date}",
                    })
                else:
                    validation_results.append({
                        "certification": required,
                        "status": "valid",
                        "expiration_date": cert.expiration_date.isoformat(),
                        "message": f"{required} certification valid until {cert.expiration_date}",
                    })
            else:
                all_valid = False
                validation_results.append({
                    "certification": required,
                    "status": "missing",
                    "message": f"Missing required {required} certification",
                })
        
        return all_valid, validation_results

    @staticmethod
    def get_user_credentials_summary(
        db: Session,
        user_id: int,
    ) -> Dict[str, Any]:
        from models.hr_personnel import Certification, CertificationStatus, Personnel
        
        personnel = db.query(Personnel).filter(
            or_(
                Personnel.email == db.query(User.email).filter(User.id == user_id).scalar_subquery(),
                Personnel.id == user_id
            )
        ).first()
        
        if not personnel:
            return {
                "user_id": user_id,
                "personnel_found": False,
                "certifications": [],
                "valid_count": 0,
                "expiring_count": 0,
                "expired_count": 0,
            }
        
        certs = db.query(Certification).filter(
            Certification.personnel_id == personnel.id
        ).all()
        
        today = date.today()
        cert_list = []
        valid_count = 0
        expiring_count = 0
        expired_count = 0
        
        for cert in certs:
            if cert.expiration_date < today:
                status = "expired"
                expired_count += 1
            elif cert.expiration_date < today + timedelta(days=30):
                status = "expiring_soon"
                expiring_count += 1
            else:
                status = "valid"
                valid_count += 1
            
            cert_list.append({
                "id": cert.id,
                "type": cert.certification_type,
                "number": cert.certification_number,
                "issuing_authority": cert.issuing_authority,
                "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                "expiration_date": cert.expiration_date.isoformat() if cert.expiration_date else None,
                "status": status,
                "days_until_expiration": (cert.expiration_date - today).days if cert.expiration_date else None,
            })
        
        return {
            "user_id": user_id,
            "personnel_id": personnel.id,
            "personnel_name": f"{personnel.first_name} {personnel.last_name}",
            "personnel_found": True,
            "certifications": cert_list,
            "valid_count": valid_count,
            "expiring_count": expiring_count,
            "expired_count": expired_count,
        }

    @staticmethod
    def validate_shift_assignment(
        db: Session,
        user_id: int,
        shift_id: int,
        enforce: bool = True,
    ) -> Dict[str, Any]:
        from models.scheduling_module import ScheduledShift, ShiftDefinition
        
        shift = db.query(ScheduledShift).filter(ScheduledShift.id == shift_id).first()
        if not shift:
            return {
                "valid": False,
                "shift_found": False,
                "message": "Shift not found",
            }
        
        required_certs = []
        if shift.definition_id:
            definition = db.query(ShiftDefinition).filter(
                ShiftDefinition.id == shift.definition_id
            ).first()
            if definition and definition.required_certifications:
                required_certs = definition.required_certifications
        
        if not required_certs:
            return {
                "valid": True,
                "shift_id": shift_id,
                "required_certifications": [],
                "validation_results": [],
                "message": "No certification requirements for this shift",
            }
        
        is_valid, results = CredentialValidationService.check_user_certifications(
            db, user_id, required_certs, shift.shift_date
        )
        
        return {
            "valid": is_valid,
            "enforce": enforce,
            "shift_id": shift_id,
            "shift_date": shift.shift_date.isoformat(),
            "required_certifications": required_certs,
            "validation_results": results,
            "can_assign": is_valid or not enforce,
            "message": "All certifications valid" if is_valid else "Certification requirements not met",
        }

    @staticmethod
    def get_qualified_users_for_shift(
        db: Session,
        shift_id: int,
        org_id: int,
    ) -> List[Dict[str, Any]]:
        from models.scheduling_module import ScheduledShift, ShiftDefinition
        from models.hr_personnel import Personnel
        
        shift = db.query(ScheduledShift).filter(ScheduledShift.id == shift_id).first()
        if not shift:
            return []
        
        required_certs = []
        if shift.definition_id:
            definition = db.query(ShiftDefinition).filter(
                ShiftDefinition.id == shift.definition_id
            ).first()
            if definition and definition.required_certifications:
                required_certs = definition.required_certifications
        
        # Limit to prevent performance issues with large personnel datasets
        # This query checks all personnel for shift qualification, so we cap at 1000
        personnel_list = db.query(Personnel).limit(1000).all()
        
        qualified = []
        for person in personnel_list:
            user = db.query(User).filter(User.email == person.email).first()
            if not user or user.org_id != org_id:
                continue
            
            is_valid, results = CredentialValidationService.check_user_certifications(
                db, user.id, required_certs, shift.shift_date
            )
            
            expiring_certs = [r for r in results if r.get("status") == "expiring_soon"]
            
            qualified.append({
                "user_id": user.id,
                "personnel_id": person.id,
                "name": f"{person.first_name} {person.last_name}",
                "email": person.email,
                "job_title": person.job_title,
                "fully_qualified": is_valid,
                "has_expiring_certs": len(expiring_certs) > 0,
                "expiring_certs_count": len(expiring_certs),
                "validation_details": results,
            })
        
        qualified.sort(key=lambda x: (not x["fully_qualified"], x["has_expiring_certs"]))
        
        return qualified


def get_credential_validation_service() -> CredentialValidationService:
    return CredentialValidationService()
