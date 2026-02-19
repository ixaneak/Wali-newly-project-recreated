"""
Celery Async Task Queue for WALI

Handles background processing:
- SAR detection (compliance)
- Email notifications
- Report generation
- Data exports

Uses Redis as broker (hosted in JNB - Johannesburg, closest to Ivory Coast)
"""

import os
from celery import Celery
from celery.signals import task_failure, task_success
import logging

logger = logging.getLogger('celery')


# ═════════════════════════════════════════════════════════════════
# CELERY APP CONFIGURATION
# ═════════════════════════════════════════════════════════════════

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app with explicit serializer configuration
celery_app = Celery(
    'wali_tasks',
    broker=redis_url,
    backend=redis_url,
    include=[
        'infrastructure.celery.tasks.sar_tasks',
        'infrastructure.celery.tasks.notification_tasks',
        'infrastructure.celery.tasks.report_tasks',
    ]
)

# Serializer configuration (required for security)
celery_app.conf.update(
    # Serializers
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # Soft limit at 50 minutes
    
    # Result backend
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    
    # Queue configuration
    task_default_queue='default',
    task_queues={
        'default': {'exchange': 'default', 'routing_key': 'default'},
        'sar': {'exchange': 'sar', 'routing_key': 'sar'},
        'notifications': {'exchange': 'notifications', 'routing_key': 'notifications'},
        'reports': {'exchange': 'reports', 'routing_key': 'reports'},
    },
    
    # Routing
    task_routes={
        'infrastructure.celery.tasks.sar_tasks.*': {'queue': 'sar'},
        'infrastructure.celery.tasks.notification_tasks.*': {'queue': 'notifications'},
        'infrastructure.celery.tasks.report_tasks.*': {'queue': 'reports'},
    },
    
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# ═════════════════════════════════════════════════════════════════
# MONITORING SIGNALS
# ═════════════════════════════════════════════════════════════════

@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, **extras):
    """Log task failures for monitoring."""
    logger.error(
        f"Task failed: {sender.name}[{task_id}]\n"
        f"Exception: {exception}\n"
        f"Args: {args}\n"
        f"Kwargs: {kwargs}"
    )


@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """Log successful task completion."""
    logger.info(f"Task completed: {sender.name}[{sender.request.id}]")


# ═════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════════

def check_celery_health() -> dict:
    """Check Celery and broker health."""
    try:
        # Ping the broker
        inspector = celery_app.control.inspect()
        active_workers = inspector.active()
        
        return {
            'status': 'healthy',
            'broker_url': redis_url.replace('://', '://***:***@') if '://' in redis_url else 'configured',
            'active_workers': len(active_workers) if active_workers else 0,
            'error': None,
        }
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
        }
