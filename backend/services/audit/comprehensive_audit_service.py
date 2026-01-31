"""
Comprehensive Audit Service for FedRAMP AU-2, AU-3, AU-9 Compliance

This service provides centralized audit logging for all security-relevant events:
- Authentication events (success/failure)
- Authorization events
- Data access events
- Data modification events
- Configuration changes
- Security events

All logs are immutable (write-only) and retained for 7 years per FedRAMP requirements.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from core.logger import logger
from models.comprehensive_audit_log import (
    AuditEventType,
    AuditOutcome,
    ComprehensiveAuditLog,
)
from models.user import User


class ComprehensiveAuditService:
    """Service for comprehensive audit logging"""

    @staticmethod
    def _extract_request_info(request: Optional[Request]) -> Dict[str, Any]:
        """Extract request information for audit logging"""
        if not request:
            return {}
        
        return {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_method": request.method,
            "request_path": str(request.url.path),
            "request_query": str(request.url.query) if request.url.query else None,
            "session_id": request.headers.get("x-session-id"),
            "device_id": request.headers.get("x-device-id"),
            "device_fingerprint": request.headers.get("x-device-fingerprint"),
        }

    @staticmethod
    def _create_audit_log(
        db: Session,
        org_id: int,
        event_type: AuditEventType,
        action: str,
        resource_type: str,
        outcome: AuditOutcome,
        user: Optional[User] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        classification: Optional[str] = None,
        training_mode: bool = False,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        reason_code: Optional[str] = None,
        decision_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAuditLog:
        """
        Create an audit log entry.
        
        This is the core method that creates immutable audit log entries.
        All audit logging should go through this method to ensure consistency.
        """
        request_info = ComprehensiveAuditService._extract_request_info(request)
        
        audit_log = ComprehensiveAuditLog(
            timestamp=datetime.now(timezone.utc),
            org_id=org_id,
            user_id=user.id if user else None,
            user_email=user.email if user else None,
            user_role=user.role if user else None,
            event_type=event_type.value,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            outcome=outcome.value,
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            request_method=request_info.get("request_method"),
            request_path=request_info.get("request_path"),
            request_query=request_info.get("request_query"),
            session_id=request_info.get("session_id"),
            device_id=request_info.get("device_id"),
            device_fingerprint=request_info.get("device_fingerprint"),
            classification=classification or "NON_PHI",
            training_mode=training_mode,
            before_state=before_state,
            after_state=after_state,
            error_message=error_message,
            error_code=error_code,
            reason_code=reason_code,
            decision_id=decision_id,
            metadata=metadata,
        )
        
        db.add(audit_log)
        try:
            db.commit()
            db.refresh(audit_log)
            return audit_log
        except Exception as e:
            db.rollback()
            logger.error(
                f"CRITICAL: Failed to write comprehensive audit log: {e}",
                exc_info=True,
            )
            # Re-raise to ensure audit failures are noticed
            raise

    @staticmethod
    def log_authentication(
        db: Session,
        org_id: int,
        action: str,  # login, logout, token_refresh, mfa_verify, etc.
        outcome: AuditOutcome,
        user: Optional[User] = None,
        request: Optional[Request] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAuditLog:
        """Log authentication events"""
        return ComprehensiveAuditService._create_audit_log(
            db=db,
            org_id=org_id,
            event_type=AuditEventType.AUTHENTICATION,
            action=action,
            resource_type="auth",
            outcome=outcome,
            user=user,
            request=request,
            error_message=error_message,
            metadata=metadata,
        )

    @staticmethod
    def log_authorization(
        db: Session,
        org_id: int,
        action: str,  # access_granted, access_denied, permission_check, etc.
        resource_type: str,
        outcome: AuditOutcome,
        user: Optional[User] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        reason_code: Optional[str] = None,
        decision_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAuditLog:
        """Log authorization events"""
        return ComprehensiveAuditService._create_audit_log(
            db=db,
            org_id=org_id,
            event_type=AuditEventType.AUTHORIZATION,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            user=user,
            resource_id=resource_id,
            request=request,
            reason_code=reason_code,
            decision_id=decision_id,
            metadata=metadata,
        )

    @staticmethod
    def log_data_access(
        db: Session,
        org_id: int,
        action: str,  # read, view, export, search, etc.
        resource_type: str,
        outcome: AuditOutcome,
        user: Optional[User] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        classification: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAuditLog:
        """Log data access events"""
        return ComprehensiveAuditService._create_audit_log(
            db=db,
            org_id=org_id,
            event_type=AuditEventType.DATA_ACCESS,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            user=user,
            resource_id=resource_id,
            request=request,
            classification=classification,
            metadata=metadata,
        )

    @staticmethod
    def log_data_modification(
        db: Session,
        org_id: int,
        action: str,  # create, update, delete, etc.
        resource_type: str,
        outcome: AuditOutcome,
        user: Optional[User] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        classification: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAuditLog:
        """Log data modification events"""
        return ComprehensiveAuditService._create_audit_log(
            db=db,
            org_id=org_id,
            event_type=AuditEventType.DATA_MODIFICATION,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            user=user,
            resource_id=resource_id,
            request=request,
            before_state=before_state,
            after_state=after_state,
            classification=classification,
            metadata=metadata,
        )

    @staticmethod
    def log_configuration_change(
        db: Session,
        org_id: int,
        action: str,  # update_setting, change_permission, modify_role, etc.
        resource_type: str,
        outcome: AuditOutcome,
        user: Optional[User] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAuditLog:
        """Log configuration change events"""
        return ComprehensiveAuditService._create_audit_log(
            db=db,
            org_id=org_id,
            event_type=AuditEventType.CONFIGURATION_CHANGE,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            user=user,
            resource_id=resource_id,
            request=request,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata,
        )

    @staticmethod
    def log_security_event(
        db: Session,
        org_id: int,
        action: str,  # password_change, mfa_enabled, session_revoked, etc.
        resource_type: str,
        outcome: AuditOutcome,
        user: Optional[User] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        reason_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAuditLog:
        """Log security events"""
        return ComprehensiveAuditService._create_audit_log(
            db=db,
            org_id=org_id,
            event_type=AuditEventType.SECURITY_EVENT,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            user=user,
            resource_id=resource_id,
            request=request,
            error_message=error_message,
            error_code=error_code,
            reason_code=reason_code,
            metadata=metadata,
        )

    @staticmethod
    def log_api_request(
        db: Session,
        org_id: int,
        action: str,  # api_request
        resource_type: str,  # endpoint name
        outcome: AuditOutcome,
        user: Optional[User] = None,
        request: Optional[Request] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveAuditLog:
        """Log API request events (for middleware automatic logging)"""
        return ComprehensiveAuditService._create_audit_log(
            db=db,
            org_id=org_id,
            event_type=AuditEventType.API_REQUEST,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            user=user,
            resource_id=None,
            request=request,
            error_message=error_message,
            error_code=error_code,
            metadata=metadata,
        )
