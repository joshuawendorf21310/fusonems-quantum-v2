from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from core.database import get_db
from models.collections_governance import (
    CollectionsGovernancePolicy, CollectionsAccount, CollectionsActionLog,
    CollectionsDecisionRequest, WriteOffRecord, CollectionsProhibitedAction,
    CollectionsPhase, WriteOffReason
)
from services.founder_billing.collections_governance_service import CollectionsGovernanceService

router = APIRouter(prefix="/api/collections-governance", tags=["Collections Governance"])


class PaymentRecordRequest(BaseModel):
    account_id: int
    payment_amount: float


class WriteOffRequest(BaseModel):
    account_id: int
    reason: str
    rationale: str


class FounderDecisionRequest(BaseModel):
    decision_request_id: int
    decision: str
    rationale: str


class GovernancePolicyResponse(BaseModel):
    version: str
    immutable: bool
    active: bool
    internal_collections_enabled: bool
    external_collections_enabled: bool
    credit_reporting_enabled: bool
    escalation_schedule: dict
    small_balance_threshold: float
    
    class Config:
        from_attributes = True


def get_governance_service(db: Session = Depends(get_db)) -> CollectionsGovernanceService:
    """Get Collections Governance Service."""
    return CollectionsGovernanceService(db)


@router.get("/policy", response_model=GovernancePolicyResponse)
async def get_governance_policy(db: Session = Depends(get_db)):
    """
    Get active immutable collections governance policy.
    
    Policy cannot be altered by AI or workflows - only by Founder.
    Defines authoritative rules for collections operations.
    """
    policy = db.query(CollectionsGovernancePolicy).filter_by(
        active=True,
        immutable=True
    ).order_by(CollectionsGovernancePolicy.version_date.desc()).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="No active governance policy found")
    
    return {
        "version": policy.version,
        "immutable": policy.immutable,
        "active": policy.active,
        "internal_collections_enabled": policy.internal_collections_enabled,
        "external_collections_enabled": policy.external_collections_enabled,
        "credit_reporting_enabled": policy.credit_reporting_enabled,
        "escalation_schedule": {
            "day_0": policy.escalation_day_0,
            "day_15": policy.escalation_day_15,
            "day_30": policy.escalation_day_30,
            "day_60": policy.escalation_day_60,
            "day_90": policy.escalation_day_90
        },
        "small_balance_threshold": policy.small_balance_threshold
    }


@router.get("/accounts")
async def list_collections_accounts(
    phase: Optional[str] = None,
    flagged_only: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List collections accounts.
    
    Phases:
    - internal: Standard internal collections
    - pre_collections: Final internal phase (90+ days)
    - decision_required: Flagged for Founder decision
    - written_off: Written off
    - resolved: Paid in full
    """
    query = db.query(CollectionsAccount)
    
    if phase:
        query = query.filter_by(current_phase=phase)
    if flagged_only:
        query = query.filter_by(flagged_for_founder_decision=True)
    
    accounts = query.order_by(CollectionsAccount.days_since_due.desc()).limit(limit).all()
    
    return [{
        "id": acc.id,
        "statement_id": acc.statement_id,
        "patient_id": acc.patient_id,
        "phase": acc.current_phase.value,
        "original_balance": acc.original_balance,
        "current_balance": acc.current_balance,
        "days_overdue": acc.days_since_due,
        "notices_sent": acc.notices_sent,
        "paused": acc.escalation_paused,
        "flagged": acc.flagged_for_founder_decision,
        "written_off": acc.written_off
    } for acc in accounts]


@router.get("/accounts/{account_id}")
async def get_account_details(account_id: int, db: Session = Depends(get_db)):
    """
    Get complete collections account details.
    
    Includes:
    - Balance history
    - All notices sent
    - Delivery proof
    - Payment attempts
    - Communication history
    - Action log
    """
    account = db.query(CollectionsAccount).options(
        joinedload(CollectionsAccount.actions)
    ).filter_by(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Actions are already loaded via joinedload, just need to sort them
    actions = sorted(account.actions, key=lambda a: a.executed_at, reverse=True)
    
    return {
        "account": {
            "id": account.id,
            "phase": account.current_phase.value,
            "original_balance": account.original_balance,
            "current_balance": account.current_balance,
            "total_paid": account.total_paid,
            "days_overdue": account.days_since_due,
            "notices_sent": account.notices_sent,
            "payment_attempts": account.payment_attempts,
            "insurance_pending": account.insurance_pending,
            "paused": account.escalation_paused,
            "pause_reason": account.pause_reason,
            "flagged": account.flagged_for_founder_decision,
            "founder_decision": account.founder_decision
        },
        "actions": [{
            "id": action.id,
            "action": action.action.value,
            "description": action.action_description,
            "executed_by": action.executed_by,
            "executed_at": action.executed_at,
            "balance_at_action": action.balance_at_action,
            "days_overdue": action.days_overdue_at_action,
            "policy_reference": action.policy_reference
        } for action in actions],
        "delivery_proof": account.delivery_proof,
        "communication_history": account.communication_history
    }


@router.post("/cycle/process")
async def process_collections_cycle(
    db: Session = Depends(get_db),
    service: CollectionsGovernanceService = Depends(get_governance_service)
):
    """
    Process collections cycle for all active accounts.
    
    AI autonomously:
    1. Calculates days overdue
    2. Determines escalation stage
    3. Sends appropriate notice (15/30/60/90 days)
    4. Respects payment pauses
    5. Flags accounts for Founder decision at 90+ days
    6. Logs all actions with policy references
    
    No external collections, credit reporting, or legal action.
    """
    service.process_collections_cycle()
    db.commit()
    
    return {"status": "Collections cycle processed"}


@router.post("/payment/record")
async def record_payment(
    request: PaymentRecordRequest,
    db: Session = Depends(get_db),
    service: CollectionsGovernanceService = Depends(get_governance_service)
):
    """
    Record payment and pause escalation.
    
    Any payment activity immediately pauses escalation per policy.
    """
    account = db.query(CollectionsAccount).filter_by(id=request.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    service.record_payment(account, request.payment_amount)
    db.commit()
    
    return {
        "account_id": account.id,
        "payment_recorded": request.payment_amount,
        "new_balance": account.current_balance,
        "escalation_paused": account.escalation_paused
    }


@router.get("/decisions/pending")
async def get_pending_decisions(db: Session = Depends(get_db)):
    """
    Get accounts flagged for Founder decision.
    
    AI presents factual summary:
    - Balance amount
    - Number of notices sent
    - Proof of delivery
    - Payment attempts
    - Insurance status
    - Communication history
    - AI recommendation with rationale
    
    No irreversible action without Founder intent.
    """
    decisions = db.query(CollectionsDecisionRequest).filter_by(
        founder_reviewed=False
    ).order_by(CollectionsDecisionRequest.requested_at.desc()).all()
    
    return [{
        "id": dec.id,
        "account_id": dec.account_id,
        "balance": dec.balance,
        "days_overdue": dec.days_overdue,
        "notices_sent": dec.notices_sent_count,
        "payment_attempts": dec.payment_attempts,
        "insurance_status": dec.insurance_status,
        "ai_recommendation": dec.ai_recommendation,
        "ai_rationale": dec.ai_recommendation_rationale,
        "requested_at": dec.requested_at
    } for dec in decisions]


@router.post("/decisions/founder")
async def process_founder_decision(
    request: FounderDecisionRequest,
    db: Session = Depends(get_db),
    service: CollectionsGovernanceService = Depends(get_governance_service)
):
    """
    Process Founder decision on flagged account.
    
    Decisions:
    - write_off: Write off balance (requires approval)
    - continue_collections: Resume internal collections
    - hold: Pause indefinitely
    - escalate: (Blocked - external collections disabled)
    """
    service.process_founder_decision(
        request.decision_request_id,
        request.decision,
        request.rationale
    )
    db.commit()
    
    return {
        "decision_id": request.decision_request_id,
        "decision": request.decision,
        "processed": True
    }


@router.post("/writeoff")
async def write_off_account(
    request: WriteOffRequest,
    founder_user_id: int,
    db: Session = Depends(get_db),
    service: CollectionsGovernanceService = Depends(get_governance_service)
):
    """
    Write off account balance.
    
    Requires Founder approval per governance policy.
    
    Reasons:
    - small_balance: Below threshold
    - cost_exceeds_balance: Collection cost > balance
    - undeliverable: Cannot contact patient
    - deceased_patient: Patient deceased
    - founder_decision: Founder discretion
    """
    account = db.query(CollectionsAccount).filter_by(id=request.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    service.write_off_account(
        account,
        WriteOffReason(request.reason),
        request.rationale,
        f"Founder (user_id: {founder_user_id})"
    )
    db.commit()
    
    return {
        "account_id": account.id,
        "written_off": True,
        "amount": account.write_off_amount,
        "reason": request.reason
    }


@router.get("/writeoffs")
async def list_writeoffs(limit: int = 100, db: Session = Depends(get_db)):
    """List all write-offs with audit trail."""
    writeoffs = db.query(WriteOffRecord).order_by(
        WriteOffRecord.created_at.desc()
    ).limit(limit).all()
    
    return [{
        "id": wo.id,
        "account_id": wo.account_id,
        "original_balance": wo.original_balance,
        "amount_paid": wo.amount_paid,
        "write_off_amount": wo.write_off_amount,
        "reason": wo.reason.value,
        "rationale": wo.detailed_rationale,
        "approved_by": wo.approved_by,
        "approved_at": wo.approved_at,
        "governance_version": wo.governance_version
    } for wo in writeoffs]


@router.get("/audit-log")
async def get_audit_log(
    account_id: Optional[int] = None,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    """
    Complete collections audit log.
    
    Every action recorded:
    - Notice sent
    - Payment received
    - Escalation paused
    - Flagged for decision
    - Written off
    - Resolved
    
    Each log entry includes:
    - Timestamp
    - Action description
    - Executed by (always AI Agent under Founder authority)
    - Governance version
    - Policy reference
    - Balance at action
    - Days overdue
    """
    query = db.query(CollectionsActionLog)
    
    if account_id:
        query = query.filter_by(account_id=account_id)
    
    logs = query.order_by(CollectionsActionLog.executed_at.desc()).limit(limit).all()
    
    return [{
        "id": log.id,
        "account_id": log.account_id,
        "action": log.action.value,
        "description": log.action_description,
        "executed_by": log.executed_by,
        "executed_at": log.executed_at,
        "governance_version": log.governance_version,
        "policy_reference": log.policy_reference,
        "balance_at_action": log.balance_at_action,
        "days_overdue": log.days_overdue_at_action,
        "reversible": log.reversible
    } for log in logs]


@router.get("/prohibited-actions")
async def get_prohibited_actions(db: Session = Depends(get_db)):
    """
    Log of blocked prohibited actions.
    
    Immutable governance blocks:
    - External collections
    - Credit bureau reporting
    - Legal action
    - Third-party referrals
    """
    blocks = db.query(CollectionsProhibitedAction).order_by(
        CollectionsProhibitedAction.attempted_at.desc()
    ).all()
    
    return [{
        "id": block.id,
        "action_attempted": block.action_attempted,
        "prohibited_reason": block.prohibited_reason,
        "attempted_by": block.attempted_by,
        "attempted_at": block.attempted_at,
        "governance_version": block.governance_version,
        "blocked": block.blocked
    } for block in blocks]


@router.get("/summary")
async def get_collections_summary(db: Session = Depends(get_db)):
    """
    Collections summary for Founder dashboard.
    
    High-level metrics:
    - Active accounts by phase
    - Total balance in collections
    - Pending Founder decisions
    - Write-offs this month
    - Escalation pause rate
    """
    from sqlalchemy import func
    
    summary = {
        "total_accounts": db.query(func.count(CollectionsAccount.id)).filter(
            CollectionsAccount.current_balance > 0
        ).scalar() or 0,
        
        "accounts_by_phase": dict(
            db.query(CollectionsAccount.current_phase, func.count(CollectionsAccount.id))
            .filter(CollectionsAccount.current_balance > 0)
            .group_by(CollectionsAccount.current_phase)
            .all()
        ),
        
        "total_balance_in_collections": db.query(
            func.sum(CollectionsAccount.current_balance)
        ).scalar() or 0,
        
        "pending_founder_decisions": db.query(func.count(CollectionsDecisionRequest.id)).filter(
            CollectionsDecisionRequest.founder_reviewed == False
        ).scalar() or 0,
        
        "accounts_paused": db.query(func.count(CollectionsAccount.id)).filter(
            CollectionsAccount.escalation_paused == True
        ).scalar() or 0,
        
        "writeoffs_this_month": db.query(func.count(WriteOffRecord.id)).filter(
            WriteOffRecord.created_at >= datetime.utcnow().replace(day=1)
        ).scalar() or 0
    }
    
    return summary
