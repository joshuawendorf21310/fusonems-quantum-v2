"""
Physical & Environmental (PE) FedRAMP Controls Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from core.database import get_db
from core.security import require_roles
from models.user import User, UserRole
from services.physical.access_authorization_service import PhysicalAccessAuthorizationService
from services.physical.access_control_service import PhysicalAccessControlService
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(prefix="/api/physical", tags=["Physical & Environmental Controls"])


class AuthorizationCreate(BaseModel):
    user_id: int
    authorization_type: str
    access_level: str
    authorized_areas: List[str]
    badge_type: str
    credential_type: str
    credential_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    justification: Optional[str] = None


class AuthorizationApprove(BaseModel):
    badge_number: Optional[str] = None


class AuthorizationRevoke(BaseModel):
    reason: str


@router.post("/authorizations", status_code=status.HTTP_201_CREATED)
def create_authorization(
    payload: AuthorizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a physical access authorization request"""
    service = PhysicalAccessAuthorizationService(db)
    
    authorization = service.create_authorization(
        org_id=user.org_id,
        user_id=payload.user_id,
        authorization_type=payload.authorization_type,
        access_level=payload.access_level,
        authorized_areas=payload.authorized_areas,
        badge_type=payload.badge_type,
        credential_type=payload.credential_type,
        credential_id=payload.credential_id,
        expires_at=payload.expires_at,
        justification=payload.justification,
        requested_by=user.id,
    )
    
    apply_training_mode(authorization, request)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="physical_access_authorization",
        classification="INTERNAL",
        after_state=model_snapshot(authorization),
        event_type="pe.authorization.created",
        event_payload={"authorization_id": authorization.id},
    )
    
    return authorization


@router.post("/authorizations/{authorization_id}/approve")
def approve_authorization(
    authorization_id: int,
    payload: AuthorizationApprove,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Approve a physical access authorization"""
    service = PhysicalAccessAuthorizationService(db)
    
    authorization = service.approve_authorization(
        authorization_id=authorization_id,
        approved_by=user.id,
        badge_number=payload.badge_number,
    )
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="approve",
        resource="physical_access_authorization",
        classification="INTERNAL",
        after_state=model_snapshot(authorization),
        event_type="pe.authorization.approved",
        event_payload={"authorization_id": authorization.id},
    )
    
    return authorization


@router.get("/authorizations")
def list_authorizations(
    user_id: Optional[int] = None,
    include_expired: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles()),
):
    """List physical access authorizations"""
    service = PhysicalAccessAuthorizationService(db)
    
    if user_id:
        return service.get_user_authorizations(
            org_id=current_user.org_id,
            user_id=user_id,
            include_expired=include_expired,
        )
    
    from models.physical_environmental import PhysicalAccessAuthorization
    from sqlalchemy import or_
    query = db.query(PhysicalAccessAuthorization).filter(
        PhysicalAccessAuthorization.org_id == current_user.org_id
    )
    
    if not include_expired:
        query = query.filter(
            or_(
                PhysicalAccessAuthorization.expires_at.is_(None),
                PhysicalAccessAuthorization.expires_at > datetime.utcnow(),
            )
        )
    
    return query.all()


@router.get("/authorizations/statistics")
def get_authorization_statistics(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get authorization statistics"""
    service = PhysicalAccessAuthorizationService(db)
    return service.get_authorization_statistics(user.org_id)


@router.get("/status")
def get_pe_controls_status(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get overall PE controls status"""
    return {
        "pe2_authorizations": "implemented",
        "pe3_access_control": "implemented",
        "pe4_transmission": "models_ready",
        "pe5_output_devices": "models_ready",
        "pe6_monitoring": "models_ready",
        "pe8_visitors": "models_ready",
        "pe9_power": "models_ready",
        "pe10_emergency_shutoff": "models_ready",
        "pe11_emergency_power": "models_ready",
        "pe12_emergency_lighting": "models_ready",
        "pe13_fire_protection": "models_ready",
        "pe14_environmental": "models_ready",
        "pe15_water": "models_ready",
        "pe16_delivery": "models_ready",
        "pe17_alternate_site": "models_ready",
        "pe18_component_location": "models_ready",
        "pe19_information_leakage": "models_ready",
        "pe20_asset_tracking": "models_ready",
    }
