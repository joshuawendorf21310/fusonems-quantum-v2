from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.agency_portal import (
    AgencyAnalyticsSnapshot,
    AgencyOnboardingStepRecord,
    AgencyPortalMessage,
    MessageCategory,
    MessagePriority,
    MessageStatus,
    ThirdPartyBillingAgency,
)
from models.user import User, UserRole

from .agency_service import (
    AgencyClaimService,
    AgencyDocumentService,
    AgencyIncidentService,
    AgencyPaymentService,
)


# Role definitions for agency portal
AGENCY_ADMIN_ROLES = ["agency_administrator", "agency_finance_viewer"]
AGENCY_OPS_ROLES = ["agency_operations"]
FOUNDER_ROLES = ["founder"]

# All agency roles (for general access)
ALL_AGENCY_ROLES = AGENCY_ADMIN_ROLES + AGENCY_OPS_ROLES


def get_agency_for_user(db: Session, user: User) -> ThirdPartyBillingAgency:
    """
    Get agency for current user with role validation
    Strict role-based access control:
    - agency_administrator: Full visibility, no control
    - agency_finance_viewer: Same as admin
    - agency_operations: Incidents + docs only, no financials
    - agency_crew: NO access to this portal
    - founder: Full visibility including internal notes
    """
    # Check if user has valid agency role
    if user.role not in ALL_AGENCY_ROLES + FOUNDER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Invalid role for agency portal",
        )

    # For founder, allow access to all agencies (for now, return first)
    if user.role in FOUNDER_ROLES:
        agency = db.query(ThirdPartyBillingAgency).first()
        if not agency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No agency found",
            )
        return agency

    # For agency users, get their specific agency
    agency = (
        db.query(ThirdPartyBillingAgency)
        .filter(ThirdPartyBillingAgency.id == user.org_id)
        .first()
    )

    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found for user",
        )

    if not agency.portal_access_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Portal access is disabled for this agency",
        )

    return agency


def require_financial_access(user: User = Depends(get_current_user)) -> User:
    """Require financial access (admin or finance viewer only)"""
    if user.role not in AGENCY_ADMIN_ROLES + FOUNDER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Financial access denied: Insufficient permissions",
        )
    return user


agency_router = APIRouter(
    prefix="/api/agency",
    tags=["Agency Portal"],
)
router = agency_router


# Pydantic models for request/response
class IncidentFilters(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    transport_priority: Optional[str] = None
    claim_status: Optional[str] = None
    limit: int = 100


class ClaimFilters(BaseModel):
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 100


class MessageCreate(BaseModel):
    category: str
    priority: str = "informational"
    subject: str
    content: str
    linked_context: Optional[dict] = None


# Founder-only: list all agencies (Wisconsin-first, US-wide)
@agency_router.get("/agencies")
def list_agencies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    List all third-party billing agencies (founder only).
    Returns state, pricing (base + per call), and summary for multi-state management.
    """
    if user.role not in FOUNDER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Founder access required",
        )
    agencies = db.query(ThirdPartyBillingAgency).order_by(ThirdPartyBillingAgency.agency_name).all()
    result = []
    for a in agencies:
        steps = (
            db.query(AgencyOnboardingStepRecord)
            .filter(AgencyOnboardingStepRecord.agency_id == a.id)
            .all()
        )
        total_steps = 10
        completed = sum(1 for s in steps if s.completed)
        onboarding_progress = int(100 * completed / total_steps) if total_steps else 0
        pending_messages = (
            db.query(AgencyPortalMessage)
            .filter(
                AgencyPortalMessage.agency_id == a.id,
                AgencyPortalMessage.status != MessageStatus.RESOLVED,
            )
            .count()
        )
        result.append({
            "id": a.id,
            "agency_name": a.agency_name,
            "contact_email": a.primary_contact_email or "",
            "onboarding_status": a.onboarding_status.value if a.onboarding_status else "not_started",
            "onboarding_progress": onboarding_progress,
            "activated_at": a.billing_activated_at.isoformat() if a.billing_activated_at else None,
            "total_accounts": 0,
            "active_accounts": 0,
            "messages_pending": pending_messages,
            "state": a.state or "",
            "service_types": list(a.service_types) if isinstance(a.service_types, list) else (list(a.service_types) if a.service_types else []),
            "base_charge_cents": a.base_charge_cents,
            "per_call_cents": a.per_call_cents,
            "billing_interval": a.billing_interval or "",
        })
    return result


# Founder-only: list all agencies' analytics
@agency_router.get("/analytics")
def list_analytics(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    List analytics per agency (founder only). Uses latest snapshot per agency.
    """
    if user.role not in FOUNDER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Founder access required",
        )
    agencies = db.query(ThirdPartyBillingAgency).order_by(ThirdPartyBillingAgency.agency_name).all()
    result = []
    for a in agencies:
        latest = (
            db.query(AgencyAnalyticsSnapshot)
            .filter(AgencyAnalyticsSnapshot.agency_id == a.id)
            .order_by(AgencyAnalyticsSnapshot.period_end.desc())
            .first()
        )
        if latest:
            result.append({
                "agency_id": a.id,
                "agency_name": a.agency_name,
                "total_statements_sent": latest.accounts_patient_responsibility + latest.accounts_insurance_pending,
                "total_collected": latest.payments_collected or 0,
                "collection_rate": latest.collection_rate or 0,
                "avg_days_to_payment": round(latest.average_days_to_pay or 0),
                "active_payment_plans": latest.accounts_payment_plan or 0,
            })
        else:
            result.append({
                "agency_id": a.id,
                "agency_name": a.agency_name,
                "total_statements_sent": 0,
                "total_collected": 0,
                "collection_rate": 0,
                "avg_days_to_payment": 0,
                "active_payment_plans": 0,
            })
    return result[:limit]


# Incident Endpoints
@agency_router.get("/incidents")
def list_incidents(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    transport_priority: Optional[str] = Query(None),
    claim_status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    List incidents for agency (read-only)
    Available to: agency_administrator, agency_finance_viewer, agency_operations, founder
    """
    agency = get_agency_for_user(db, user)

    filters = {
        "start_date": datetime.fromisoformat(start_date) if start_date else None,
        "end_date": datetime.fromisoformat(end_date) if end_date else None,
        "transport_priority": transport_priority,
        "claim_status": claim_status,
        "limit": limit,
    }

    incidents = AgencyIncidentService.get_incidents(db, agency, filters)

    return {
        "agency_id": agency.id,
        "agency_name": agency.agency_name,
        "incidents": incidents,
        "count": len(incidents),
    }


@agency_router.get("/incidents/{incident_id}")
def get_incident_detail(
    incident_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get single incident with safe data only
    Available to: agency_administrator, agency_finance_viewer, agency_operations, founder
    """
    agency = get_agency_for_user(db, user)

    incident = AgencyIncidentService.get_incident_detail(db, agency, incident_id)

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return incident


@agency_router.get("/incidents/{incident_id}/documentation")
def get_incident_documentation(
    incident_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get documentation status for incident
    Available to: agency_administrator, agency_finance_viewer, agency_operations, founder
    """
    agency = get_agency_for_user(db, user)

    documentation = AgencyDocumentService.get_documentation_status(db, agency, incident_id)

    if not documentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return documentation


@agency_router.get("/incidents/{incident_id}/claim")
def get_incident_claim(
    incident_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_financial_access),
):
    """
    Get claim status for incident
    Available to: agency_administrator, agency_finance_viewer, founder
    """
    agency = get_agency_for_user(db, user)

    # Find claim for incident
    from models.billing_claims import BillingClaim

    claim = (
        db.query(BillingClaim)
        .filter(
            BillingClaim.org_id == agency.id,
            BillingClaim.epcr_patient_id == incident_id,
        )
        .first()
    )

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No claim found for this incident",
        )

    claim_status = AgencyClaimService.get_claim_status(db, agency, claim.id)

    return claim_status


@agency_router.get("/incidents/{incident_id}/why-not-paid")
def get_why_not_paid(
    incident_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_financial_access),
):
    """
    Explainer panel for why incident hasn't been paid
    Available to: agency_administrator, agency_finance_viewer, founder
    """
    agency = get_agency_for_user(db, user)

    # Find claim for incident
    from models.billing_claims import BillingClaim

    claim = (
        db.query(BillingClaim)
        .filter(
            BillingClaim.org_id == agency.id,
            BillingClaim.epcr_patient_id == incident_id,
        )
        .first()
    )

    if not claim:
        return {
            "incident_id": incident_id,
            "reason": "No claim has been created for this incident yet",
            "status": "not_started",
            "next_steps": ["Complete incident documentation", "Submit for billing review"],
        }

    reasons = []
    next_steps = []

    if claim.status == "draft":
        reasons.append("Claim is in draft status and has not been submitted")
        next_steps.append("Complete claim review and submit to payer")
    elif claim.status == "submitted":
        reasons.append("Claim has been submitted and is pending with payer")
        next_steps.append("Wait for payer response (typically 14-30 days)")
    elif claim.status == "pending":
        reasons.append("Claim is pending with payer for review")
        next_steps.append("Follow up with payer if over 30 days")
    elif claim.status == "denied":
        reasons.append(f"Claim was denied: {claim.denial_reason or 'Reason not specified'}")
        next_steps.append("Review denial reason")
        next_steps.append("Submit appeal if appropriate")
    elif claim.status == "paid":
        reasons.append("Claim has been paid")
        next_steps = []

    return {
        "incident_id": incident_id,
        "claim_id": claim.id,
        "status": claim.status,
        "reasons": reasons,
        "next_steps": next_steps,
        "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
        "payer_name": claim.payer_name,
    }


# Claim Endpoints
@agency_router.get("/claims")
def list_claims(
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(require_financial_access),
):
    """
    List all claims for agency
    Available to: agency_administrator, agency_finance_viewer, founder
    """
    agency = get_agency_for_user(db, user)

    filters = {
        "status": status,
        "start_date": datetime.fromisoformat(start_date) if start_date else None,
        "end_date": datetime.fromisoformat(end_date) if end_date else None,
        "limit": limit,
    }

    claims = AgencyClaimService.get_claims_list(db, agency, filters)

    return {
        "agency_id": agency.id,
        "agency_name": agency.agency_name,
        "claims": claims,
        "count": len(claims),
    }


@agency_router.get("/claims/{claim_id}")
def get_claim_detail(
    claim_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_financial_access),
):
    """
    Get claim detail with timeline
    Available to: agency_administrator, agency_finance_viewer, founder
    """
    agency = get_agency_for_user(db, user)

    claim_status = AgencyClaimService.get_claim_status(db, agency, claim_id)
    claim_timeline = AgencyClaimService.get_claim_timeline(db, agency, claim_id)

    if not claim_status or not claim_timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    return {
        **claim_status,
        "timeline": claim_timeline["timeline"],
    }


# Payment Endpoints
@agency_router.get("/payments")
def list_payments(
    claim_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_financial_access),
):
    """
    List payment history for agency or specific claim
    Available to: agency_administrator, agency_finance_viewer, founder
    """
    agency = get_agency_for_user(db, user)

    payments = AgencyPaymentService.get_payments(db, agency, claim_id)

    return {
        "agency_id": agency.id,
        "agency_name": agency.agency_name,
        "payments": payments,
        "count": len(payments),
    }


@agency_router.get("/payments/summary")
def get_payment_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_financial_access),
):
    """
    Get payment summary with totals and balances
    Available to: agency_administrator, agency_finance_viewer, founder
    """
    agency = get_agency_for_user(db, user)

    summary = AgencyPaymentService.get_payment_summary(db, agency)

    return {
        "agency_id": agency.id,
        "agency_name": agency.agency_name,
        **summary,
    }


# Message Endpoints
@agency_router.get("/messages")
def list_messages(
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    all_agencies: bool = Query(False, alias="all"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get message inbox for agency. Founder can use ?all=true to get all agencies' messages (flat list).
    """
    # Founder: optional flat list of all agencies' messages
    if all_agencies and user.role in FOUNDER_ROLES:
        query = db.query(AgencyPortalMessage, ThirdPartyBillingAgency).join(
            ThirdPartyBillingAgency,
            AgencyPortalMessage.agency_id == ThirdPartyBillingAgency.id,
        )
        if status_filter:
            try:
                status_enum = MessageStatus(status_filter)
                query = query.filter(AgencyPortalMessage.status == status_enum)
            except ValueError:
                pass
        if category:
            try:
                cat_enum = MessageCategory(category)
                query = query.filter(AgencyPortalMessage.category == cat_enum)
            except ValueError:
                pass
        rows = query.order_by(AgencyPortalMessage.received_at.desc()).limit(limit).all()
        return [
            {
                "id": msg.id,
                "agency_id": msg.agency_id,
                "agency_name": agency.agency_name,
                "subject": msg.subject,
                "message_body": msg.content,
                "category": msg.category.value,
                "priority": msg.priority.value,
                "ai_triaged": msg.ai_triaged or False,
                "ai_suggested_response": msg.ai_suggested_response,
                "status": msg.status.value,
                "created_at": msg.received_at.isoformat(),
            }
            for msg, agency in rows
        ]
    agency = get_agency_for_user(db, user)
    query = db.query(AgencyPortalMessage).filter(
        AgencyPortalMessage.agency_id == agency.id
    )
    if status_filter:
        try:
            status_enum = MessageStatus(status_filter)
            query = query.filter(AgencyPortalMessage.status == status_enum)
        except ValueError:
            pass
    if category:
        try:
            cat_enum = MessageCategory(category)
            query = query.filter(AgencyPortalMessage.category == cat_enum)
        except ValueError:
            pass
    messages = query.order_by(AgencyPortalMessage.received_at.desc()).limit(limit).all()
    return {
        "agency_id": agency.id,
        "agency_name": agency.agency_name,
        "messages": [
            {
                "id": msg.id,
                "thread_id": msg.thread_id,
                "category": msg.category.value,
                "priority": msg.priority.value,
                "status": msg.status.value,
                "subject": msg.subject,
                "sender_name": msg.sender_name,
                "received_at": msg.received_at.isoformat(),
                "acknowledged_at": msg.acknowledged_at.isoformat() if msg.acknowledged_at else None,
                "responded_at": msg.responded_at.isoformat() if msg.responded_at else None,
            }
            for msg in messages
        ],
        "count": len(messages),
    }


@agency_router.post("/messages", status_code=status.HTTP_201_CREATED)
def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Send message to FusionEMS (only allowed write action)
    Available to: all agency roles, founder
    """
    agency = get_agency_for_user(db, user)

    # Validate category
    try:
        category_enum = MessageCategory(message.category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {message.category}",
        )

    # Validate priority
    try:
        priority_enum = MessagePriority(message.priority)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority: {message.priority}",
        )

    # Generate thread ID
    thread_id = f"thread_{agency.id}_{int(datetime.utcnow().timestamp())}"

    # Create message
    new_message = AgencyPortalMessage(
        agency_id=agency.id,
        thread_id=thread_id,
        category=category_enum,
        priority=priority_enum,
        subject=message.subject,
        content=message.content,
        sender_type="agency",
        sender_name=user.full_name if hasattr(user, "full_name") else "Agency User",
        linked_context=message.linked_context or {},
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {
        "message_id": new_message.id,
        "thread_id": new_message.thread_id,
        "status": new_message.status.value,
        "created_at": new_message.created_at.isoformat(),
        "message": "Message sent successfully",
    }


@agency_router.get("/messages/{message_id}")
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get single message with full content
    Available to: all agency roles, founder
    """
    agency = get_agency_for_user(db, user)

    message = (
        db.query(AgencyPortalMessage)
        .filter(
            AgencyPortalMessage.agency_id == agency.id,
            AgencyPortalMessage.id == message_id,
        )
        .first()
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    return {
        "id": message.id,
        "thread_id": message.thread_id,
        "category": message.category.value,
        "priority": message.priority.value,
        "status": message.status.value,
        "subject": message.subject,
        "content": message.content,
        "sender_type": message.sender_type,
        "sender_name": message.sender_name,
        "received_at": message.received_at.isoformat(),
        "acknowledged_at": message.acknowledged_at.isoformat() if message.acknowledged_at else None,
        "responded_at": message.responded_at.isoformat() if message.responded_at else None,
        "resolved_at": message.resolved_at.isoformat() if message.resolved_at else None,
        "linked_context": message.linked_context,
    }
