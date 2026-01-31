"""
Audit Middleware for Automatic API Request Logging

This middleware automatically logs all API requests to the comprehensive
audit log system for FedRAMP compliance. It captures:
- All API requests (method, path, query)
- User identification
- IP address and user-agent
- Request outcome (success/failure)
- Error details

The middleware should be added early in the middleware stack to capture
all requests, including authentication failures.
"""
import time
from typing import Callable

from fastapi import Request, Response, status
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.logger import logger
from models.comprehensive_audit_log import AuditOutcome
from services.audit.comprehensive_audit_service import ComprehensiveAuditService


# Paths that should not be audited (health checks, static files, etc.)
EXCLUDED_PATHS = {
    "/healthz",
    "/health",
    "/api/health",
    "/api/health/telnyx",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
}


def should_audit_path(path: str) -> bool:
    """Determine if a path should be audited"""
    # Exclude health checks and documentation
    if path in EXCLUDED_PATHS:
        return False
    
    # Exclude static file paths
    if path.startswith("/static/") or path.startswith("/assets/"):
        return False
    
    # Only audit API paths
    if not path.startswith("/api/"):
        return False
    
    return True


async def audit_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to automatically log all API requests to comprehensive audit log.
    
    This middleware:
    1. Captures request information
    2. Processes the request
    3. Logs the request with outcome
    4. Handles errors gracefully (audit logging should never break requests)
    """
    # Skip audit logging for excluded paths
    if not should_audit_path(request.url.path):
        return await call_next(request)
    
    # Skip audit logging in test environment unless explicitly enabled
    if settings.ENV.lower() == "test" and not getattr(settings, "ENABLE_AUDIT_IN_TEST", False):
        return await call_next(request)
    
    start_time = time.time()
    user = None
    org_id = None
    outcome = AuditOutcome.SUCCESS
    error_message = None
    error_code = None
    status_code = None
    
    # Try to get user from request state (set by get_current_user dependency)
    try:
        user = getattr(request.state, "user", None)
        if user:
            org_id = user.org_id
    except Exception:
        pass
    
    # Try to get org_id from request state if user not available
    if not org_id:
        try:
            org_id = getattr(request.state, "org_id", None)
        except Exception:
            pass
    
    # Default org_id for unauthenticated requests (system events)
    if not org_id:
        org_id = 0  # System-level events
    
    # Process request
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # Determine outcome based on status code
        if status_code >= 500:
            outcome = AuditOutcome.ERROR
            error_code = f"HTTP_{status_code}"
        elif status_code == 401:
            outcome = AuditOutcome.DENIED
            error_code = "UNAUTHORIZED"
        elif status_code == 403:
            outcome = AuditOutcome.DENIED
            error_code = "FORBIDDEN"
        elif status_code >= 400:
            outcome = AuditOutcome.FAILURE
            error_code = f"HTTP_{status_code}"
        else:
            outcome = AuditOutcome.SUCCESS
        
        return response
        
    except Exception as e:
        # Request processing failed
        outcome = AuditOutcome.ERROR
        error_message = str(e)
        error_code = type(e).__name__
        status_code = 500
        
        # Re-raise the exception so FastAPI can handle it
        raise
    
    finally:
        # Log the request (in finally block to ensure it always runs)
        try:
            # Get database session using dependency injection pattern
            from core.database import create_session
            
            db = create_session()
            try:
                # Calculate request duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Determine resource type from path
                resource_type = request.url.path
                if resource_type.startswith("/api/"):
                    # Extract service name from path (e.g., /api/auth/login -> auth)
                    parts = resource_type.split("/")
                    if len(parts) > 2:
                        resource_type = parts[2]  # Service name
                
                # Log the API request
                ComprehensiveAuditService.log_api_request(
                    db=db,
                    org_id=org_id,
                    action=f"{request.method} {request.url.path}",
                    resource_type=resource_type,
                    outcome=outcome,
                    user=user,
                    request=request,
                    error_message=error_message,
                    error_code=error_code,
                    metadata={
                        "duration_ms": duration_ms,
                        "status_code": status_code,
                        "content_length": getattr(request.state, "content_length", None),
                    },
                )
            except Exception as audit_error:
                # Log audit failure but don't break the request
                logger.error(
                    f"Failed to write audit log for request {request.url.path}: {audit_error}",
                    exc_info=True,
                )
                db.rollback()
            finally:
                # Close database session
                db.close()
                    
        except Exception as e:
            # If we can't even get a DB session, log but don't break
            logger.error(
                f"Failed to get DB session for audit logging: {e}",
                exc_info=True,
            )
