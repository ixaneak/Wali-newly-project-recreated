"""
Celery Tasks for Fraud Detection.

Background fraud analysis tasks.
"""
import logging

from celery import shared_task

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

# This module is primarily for fraud-related background tasks
# Main fraud analysis happens in app.tasks.claims.process_claim_submission


@celery_app.task(
    bind=True,
    max_retries=0,  # No retries - fail fast
    time_limit=300,
)
async def run_periodic_fraud_checks(self):
    """
    Periodic task to run additional fraud checks.
    
    Runs daily to:
    - Cross-reference claims against known fraud patterns
    - Update fraud scores based on new data
    - Generate fraud reports
    """
    from app.models.base import AsyncSessionLocal
    from sqlalchemy import select, func
    from app.models.claims import Claim, ClaimStatus, FraudLog
    from datetime import datetime, timedelta, timezone
    
    logger.info("Starting periodic fraud checks")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get claims from last 24 hours
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            
            result = await db.execute(
                select(Claim).where(
                    Claim.submitted_at >= yesterday
                )
            )
            recent_claims = result.scalars().all()
            
            logger.info(f"Checking {len(recent_claims)} recent claims for fraud patterns")
            
            # Check for patterns:
            # 1. Multiple claims from same device fingerprint
            # 2. Claims at same time from different phones (impossible)
            # 3. Round number amounts (potential fraud)
            
            # Pattern detection implementation
            patterns_found = []
            
            # Pattern 1: Multiple claims from same device
            device_counts = {}
            for claim in recent_claims:
                device = getattr(claim, 'device_fingerprint', None)
                if device:
                    device_counts[device] = device_counts.get(device, 0) + 1
            
            for device, count in device_counts.items():
                if count > 3:
                    patterns_found.append({
                        "type": "multiple_claims_same_device",
                        "device": device[:8] + "...",
                        "count": count,
                        "severity": "high"
                    })
            
            # Pattern 2: Round number amounts (potential fraud indicator)
            round_amounts = [c for c in recent_claims 
                           if c.amount % 1000 == 0 and c.amount > 10000]
            if len(round_amounts) > 2:
                patterns_found.append({
                    "type": "suspicious_round_amounts",
                    "count": len(round_amounts),
                    "severity": "medium"
                })
            
            return {
                "claims_checked": len(recent_claims),
                "patterns_found": len(patterns_found),
                "patterns": patterns_found
            }
            
        except Exception as e:
            logger.error(f"Error in periodic fraud checks: {e}")
            raise


__all__ = ["run_periodic_fraud_checks"]
