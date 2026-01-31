"""
Account Lifecycle Management Job
Scheduled job for FedRAMP AC-2(2), AC-2(3) compliance.

This job should be run daily via cron or scheduler to:
- Check for inactive accounts
- Send deactivation warnings
- Disable accounts that exceed inactivity threshold
- Generate compliance reports
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.auth.account_lifecycle_service import AccountLifecycleService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_account_lifecycle_check() -> dict:
    """
    Main job function to check and manage account lifecycle.
    This function can be called directly or via cron endpoint.
    
    Returns:
        Dict with execution results
    """
    db: Session = SessionLocal()
    
    try:
        logger.info("Starting account lifecycle check job")
        
        service = AccountLifecycleService(db)
        
        # Check for inactive accounts and process them
        results = service.check_inactive_accounts()
        
        logger.info(
            "Account lifecycle check completed",
            extra={
                "notifications_sent": results["notifications_sent"],
                "accounts_disabled": results["accounts_disabled"],
                "errors": results["errors"],
                "event_type": "job.account_lifecycle_check",
            }
        )
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"Account lifecycle check job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
    finally:
        db.close()


def generate_compliance_report(org_id: int = None) -> dict:
    """
    Generate access review compliance report.
    
    Args:
        org_id: Optional organization ID to filter by
        
    Returns:
        Dict with report data
    """
    db: Session = SessionLocal()
    
    try:
        logger.info(f"Generating compliance report for org_id={org_id}")
        
        service = AccountLifecycleService(db)
        report = service.generate_access_review_report(org_id=org_id)
        
        logger.info(
            "Compliance report generated",
            extra={
                "org_id": org_id,
                "total_accounts": report["total_accounts"],
                "event_type": "job.compliance_report",
            }
        )
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "report": report,
        }
        
    except Exception as e:
        logger.error(f"Compliance report generation failed: {e}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
    finally:
        db.close()


if __name__ == "__main__":
    # Allow running directly for testing
    result = run_account_lifecycle_check()
    print(f"Job result: {result}")
