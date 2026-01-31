"""Admin endpoints for account lockout and session management (FedRAMP AC-7, AC-11/AC-12)"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.security import require_roles, get_current_user
from models.user import User, UserRole
from services.auth.account_lockout_service import AccountLockoutService
from services.auth.session_management_service import SessionManagementService


router = APIRouter(prefix="/api/auth/admin", tags=["Auth Admin"])


class UnlockAccountPayload(BaseModel):
    user_id: int
    reason: str = "admin_unlock"


class TerminateSessionPayload(BaseModel):
    session_id: Optional[int] = None
    jwt_jti: Optional[str] = None
    user_id: Optional[int] = None
    reason: str = "admin_termination"


class TerminateAllSessionsPayload(BaseModel):
    user_id: int
    reason: str = "admin_termination"


@router.post("/unlock-account")
def unlock_account(
    payload: UnlockAccountPayload,
    db: Session = Depends(get_db),
    request: Request = None,
    admin_user: User = Depends(require_roles(UserRole.admin, UserRole.ops_admin, UserRole.founder)),
):
    """Unlock a locked account (admin action) - FedRAMP AC-7"""
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify admin has access to user's organization
    if admin_user.org_id != target_user.org_id and admin_user.role != UserRole.founder.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot unlock user from different organization")
    
    success = AccountLockoutService.unlock_account(
        db=db,
        user_id=payload.user_id,
        admin_user=admin_user,
        reason=payload.reason,
        request=request,
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is not locked")
    
    return {"status": "ok", "message": f"Account unlocked for user {payload.user_id}"}


@router.get("/account-lockout-info/{user_id}")
def get_account_lockout_info(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.admin, UserRole.ops_admin, UserRole.founder)),
):
    """Get account lockout information - FedRAMP AC-7"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify admin has access to user's organization
    if admin_user.org_id != target_user.org_id and admin_user.role != UserRole.founder.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access user from different organization")
    
    lockout_info = AccountLockoutService.get_lockout_info(db, user_id)
    return lockout_info or {"is_locked": False, "failed_attempts": 0}


@router.post("/terminate-session")
def terminate_session(
    payload: TerminateSessionPayload,
    db: Session = Depends(get_db),
    request: Request = None,
    admin_user: User = Depends(require_roles(UserRole.admin, UserRole.ops_admin, UserRole.founder)),
):
    """Terminate a specific session - FedRAMP AC-11/AC-12"""
    success = SessionManagementService.terminate_session(
        db=db,
        session_id=payload.session_id,
        jwt_jti=payload.jwt_jti,
        user_id=payload.user_id,
        reason=payload.reason,
        admin_user=admin_user,
        request=request,
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or already terminated")
    
    return {"status": "ok", "message": "Session terminated"}


@router.post("/terminate-all-sessions")
def terminate_all_sessions(
    payload: TerminateAllSessionsPayload,
    db: Session = Depends(get_db),
    request: Request = None,
    admin_user: User = Depends(require_roles(UserRole.admin, UserRole.ops_admin, UserRole.founder)),
):
    """Terminate all sessions for a user - FedRAMP AC-11/AC-12"""
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify admin has access to user's organization
    if admin_user.org_id != target_user.org_id and admin_user.role != UserRole.founder.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot terminate sessions for user from different organization")
    
    count = SessionManagementService.terminate_all_user_sessions(
        db=db,
        user_id=payload.user_id,
        reason=payload.reason,
        admin_user=admin_user,
        request=request,
    )
    
    return {"status": "ok", "message": f"Terminated {count} sessions", "sessions_terminated": count}


@router.get("/user-sessions/{user_id}")
def get_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.admin, UserRole.ops_admin, UserRole.founder)),
):
    """Get all active sessions for a user - FedRAMP AC-11/AC-12"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify admin has access to user's organization
    if admin_user.org_id != target_user.org_id and admin_user.role != UserRole.founder.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access user from different organization")
    
    sessions = SessionManagementService.get_user_active_sessions(db, user_id)
    return {
        "user_id": user_id,
        "sessions": [SessionManagementService.get_session_info(session) for session in sessions],
        "count": len(sessions),
    }
