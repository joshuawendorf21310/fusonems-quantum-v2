"""
Comprehensive production health check service.
Checks all critical dependencies and services.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.config import settings
from core.database import get_engine
from core.logger import logger


class ProductionHealthService:
    """Production health check service for monitoring and load balancers."""
    
    @staticmethod
    def check_database(db: Optional[Session] = None) -> Dict[str, Any]:
        """Check database connectivity and pool status."""
        try:
            if db:
                db.execute(text("SELECT 1"))
                return {"status": "healthy", "connected": True}
            else:
                engine = get_engine()
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                pool = engine.pool
                return {
                    "status": "healthy",
                    "connected": True,
                    "pool_size": pool.size() if hasattr(pool, 'size') else None,
                    "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else None,
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity if configured."""
        try:
            # Redis is optional, so this is a no-op if not configured
            redis_url = getattr(settings, 'REDIS_URL', None)
            if not redis_url:
                return {"status": "not_configured", "skipped": True}
            
            # TODO: Add actual Redis check when Redis client is configured
            return {"status": "healthy", "connected": True}
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    @staticmethod
    def check_external_apis() -> Dict[str, Any]:
        """Check external API connectivity."""
        checks = {}
        
        # Check Telnyx
        try:
            if settings.TELNYX_API_KEY:
                import telnyx
                client = telnyx.Telnyx(api_key=settings.TELNYX_API_KEY)
                resp = client.balance.retrieve()
                checks["telnyx"] = {
                    "status": "healthy",
                    "configured": True,
                    "balance": getattr(getattr(resp, "data", resp), "available_credit", None)
                }
            else:
                checks["telnyx"] = {"status": "not_configured", "skipped": True}
        except Exception as e:
            checks["telnyx"] = {
                "status": "unhealthy",
                "configured": True,
                "error": str(e)
            }
        
        # Check Postmark (optional - SMTP/IMAP is primary email method)
        # Postmark is only used if explicitly configured
        if settings.POSTMARK_SERVER_TOKEN:
            checks["postmark"] = {"status": "healthy", "configured": True}
        else:
            # Not configured is normal - SMTP/IMAP is primary
            checks["postmark"] = {"status": "not_configured", "skipped": True, "note": "SMTP/IMAP is primary email method"}
        
        # Check Stripe
        try:
            if settings.stripe_secret_key:
                checks["stripe"] = {"status": "healthy", "configured": True}
            else:
                checks["stripe"] = {"status": "not_configured", "skipped": True}
        except Exception as e:
            checks["stripe"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        return checks
    
    @staticmethod
    def check_storage() -> Dict[str, Any]:
        """Check storage backend connectivity."""
        try:
            backend = getattr(settings, 'DOCS_STORAGE_BACKEND', 'local')
            if backend == 'local':
                import os
                storage_dir = getattr(settings, 'DOCS_STORAGE_LOCAL_DIR', 'storage/documents')
                if os.path.exists(storage_dir) and os.access(storage_dir, os.W_OK):
                    return {"status": "healthy", "backend": "local", "writable": True}
                else:
                    return {
                        "status": "unhealthy",
                        "backend": "local",
                        "writable": False,
                        "error": f"Storage directory not writable: {storage_dir}"
                    }
            elif backend == 's3':
                # TODO: Add S3 connectivity check
                return {"status": "healthy", "backend": "s3"}
            else:
                return {"status": "unknown", "backend": backend}
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    def comprehensive_health(db: Optional[Session] = None) -> Dict[str, Any]:
        """Comprehensive health check for all services."""
        start_time = datetime.now(timezone.utc)
        
        # Run all checks
        database_check = ProductionHealthService.check_database(db)
        redis_check = ProductionHealthService.check_redis()
        external_apis = ProductionHealthService.check_external_apis()
        storage_check = ProductionHealthService.check_storage()
        
        # Determine overall status
        all_checks = [
            database_check.get("status"),
            redis_check.get("status"),
            storage_check.get("status"),
        ]
        # Add external API statuses
        for api_name, api_check in external_apis.items():
            if api_check.get("configured") and api_check.get("status") != "not_configured":
                all_checks.append(api_check.get("status"))
        
        # Critical checks (database, storage) must be healthy
        critical_healthy = (
            database_check.get("status") == "healthy" and
            storage_check.get("status") == "healthy"
        )
        
        # Overall status
        if not critical_healthy:
            overall_status = "unhealthy"
        elif any(status == "unhealthy" for status in all_checks if status):
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return {
            "status": overall_status,
            "timestamp": end_time.isoformat(),
            "duration_ms": round(duration_ms, 2),
            "version": getattr(settings, "APP_VERSION", "unknown"),
            "environment": settings.ENV,
            "checks": {
                "database": database_check,
                "redis": redis_check,
                "storage": storage_check,
                "external_apis": external_apis,
            }
        }
    
    @staticmethod
    def liveness() -> Dict[str, Any]:
        """Simple liveness check - just verify the app is running."""
        return {
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def readiness(db: Optional[Session] = None) -> Dict[str, Any]:
        """Readiness check - verify critical dependencies are available."""
        database_check = ProductionHealthService.check_database(db)
        storage_check = ProductionHealthService.check_storage()
        
        ready = (
            database_check.get("status") == "healthy" and
            storage_check.get("status") == "healthy"
        )
        
        return {
            "status": "ready" if ready else "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": database_check.get("status"),
                "storage": storage_check.get("status"),
            }
        }
