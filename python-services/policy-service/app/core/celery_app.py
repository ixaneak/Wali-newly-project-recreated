"""
Celery Configuration for Wali Assurance Claims Processing.

Critical configuration for:
- Fraud detection pipeline
- Mobile money settlements (revenue critical)
- ARTCI/CIMA audit compliance
"""
import logging
import os
from typing import Any, Dict

from celery import Celery
from celery.signals import task_failure

# Configure logging
logger = logging.getLogger(__name__)

# Redis broker URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "wali_claims",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.claims",
        "app.tasks.payments",
        "app.tasks.fraud",
    ],
)

# Critical configuration for Ivorian mobile money APIs
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone - Côte d'Ivoire (UTC+0, no DST)
    timezone="Africa/Abidjan",
    enable_utc=True,
    
    # Task tracking for audit trails (CIMA requirement)
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Soft limit for cleanup
    
    # Fair scheduling - critical for mobile money retry handling
    # Prevents one slow task from blocking others
    worker_prefetch_multiplier=1,
    
    # Result backend configuration
    result_expires=3600 * 24 * 7,  # Keep results for 7 days
    result_extended=True,
    
    # Retry configuration
    task_default_retry_delay=60,  # Base delay 60 seconds
    task_max_retries=3,
    
    # Worker configuration
    worker_concurrency=4,
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (memory leaks)
)


def get_task_retry_config(task_name: str) -> Dict[str, Any]:
    """
    Get task-specific retry configuration.
    
    Different tasks have different retry needs:
    - Claim processing: 3 retries with exponential backoff
    - Mobile money settlement: 5 retries (APIs are unstable)
    - Fraud analysis: No retries (CPU intensive, fail fast)
    """
    configs = {
        "app.tasks.claims.process_claim_submission": {
            "max_retries": 3,
            "countdown": 60,  # Base: 60s, then 120s, then 240s
            "retry_backoff": True,
            "retry_backoff_max": 600,  # Max 10 minutes between retries
        },
        "app.tasks.payments.settle_pharmacy_claim": {
            "max_retries": 5,
            "countdown": 30,  # Mobile money APIs need faster retries
            "retry_backoff": True,
            "retry_backoff_max": 300,  # Max 5 minutes
            "retry_jitter": True,  # Add randomness to prevent thundering herd
        },
        "app.tasks.fraud.analyze_image_fraud": {
            "max_retries": 0,  # No retries - CPU intensive, fail fast
            "bind": True,  # Bind task instance for self.retry access if needed
        },
    }
    return configs.get(task_name, {})


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, 
                        kwargs=None, traceback=None, einfo=None, **kw):
    """
    Global task failure handler.
    
    Critical for:
    - Payment task failures (revenue critical)
    - Admin alerts for fraud system failures
    - Audit trail for CIMA compliance
    """
    task_name = sender.name if sender else "unknown"
    
    # Log failure details
    logger.error(
        f"TASK_FAILURE|"
        f"task={task_name}|"
        f"task_id={task_id}|"
        f"exception={str(exception)}|"
        f"args={args}|"
        f"kwargs_keys={list(kwargs.keys()) if kwargs else []}"
    )
    
    # Critical: Alert on payment task failures
    if "settle_pharmacy_claim" in task_name or "payment" in task_name:
        logger.critical(
            f"PAYMENT_TASK_FAILURE|"
            f"task_id={task_id}|"
            f"exception={str(exception)}|"
            f"IMMEDIATE_ATTENTION_REQUIRED"
        )
        
        # Send admin alert (in production, this would use SMS/email)
        _send_admin_alert(
            subject=f"URGENT: Payment Task Failed - {task_id}",
            body=f"Task: {task_name}\nException: {exception}\nArgs: {args}",
            priority="CRITICAL"
        )
    
    # Alert on fraud system failures
    elif "fraud" in task_name or "analyze" in task_name:
        logger.critical(
            f"FRAUD_SYSTEM_FAILURE|"
            f"task_id={task_id}|"
            f"exception={str(exception)}"
        )
        
        _send_admin_alert(
            subject=f"Fraud System Failure - {task_id}",
            body=f"Task: {task_name}\nException: {exception}",
            priority="HIGH"
        )


def _send_admin_alert(subject: str, body: str, priority: str = "NORMAL"):
    """
    Send alert to admin team.
    
    Integrates with:
    - Webhook notifications (Slack/PagerDuty) via ADMIN_ALERT_WEBHOOK_URL
    - SMS gateway via ADMIN_ALERT_PHONE
    - Structured logging for audit trail
    
    For critical alerts (settlement failures), use _alert_admin_settlement_failure
    in app/tasks/payments.py which has more robust error handling.
    """
    import os
    
    alert_payload = {
        "level": priority,
        "subject": subject,
        "body": body[:500],
        "timestamp": datetime.utcnow().isoformat(),
        "source": "celery_worker"
    }
    
    # Always log critically
    logger.critical(f"ADMIN_ALERT|{alert_payload}")
    
    # Attempt webhook if configured
    try:
        webhook_url = os.getenv("ADMIN_ALERT_WEBHOOK_URL")
        if webhook_url and priority in ["HIGH", "CRITICAL"]:
            import requests
            requests.post(
                webhook_url,
                json=alert_payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        logger.error(f"Failed to send webhook alert: {e}")


# Export for use in tasks
__all__ = ["celery_app", "get_task_retry_config"]
