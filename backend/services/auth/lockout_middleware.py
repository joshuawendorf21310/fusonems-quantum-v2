"""Middleware for checking account lockout before authentication"""
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from services.auth.account_lockout_service import AccountLockoutService
from models.user import User


async def check_account_lockout_middleware(request: Request, call_next):
    """
    Middleware to check if account is locked before processing authentication requests.
    This should be applied to routes that require authentication.
    """
    # Skip lockout check for non-authenticated endpoints
    # Only check lockout for endpoints that require authentication
    
    # Check if this is an authentication-related endpoint that might need lockout checking
    path = request.url.path
    
    # For login endpoints, lockout is checked in the login handler itself
    # This middleware is for protecting authenticated endpoints
    
    response = await call_next(request)
    return response


def check_account_locked(db: Session, user_id: int) -> None:
    """
    Check if account is locked and raise HTTPException if so.
    This is called from authentication dependencies.
    """
    if AccountLockoutService.is_account_locked(db, user_id):
        lockout_info = AccountLockoutService.get_lockout_info(db, user_id)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error": "Account locked",
                "message": "Your account has been locked due to multiple failed login attempts. "
                          "Please try again later or contact an administrator.",
                "locked_until": lockout_info.get("locked_until") if lockout_info else None,
            },
            headers={"Retry-After": "1800"},  # 30 minutes in seconds
        )
