"""
Celery Tasks for Payment Settlement.

Mobile money disbursement tasks:
- Pharmacy claim settlement
- Retry logic for unstable APIs
- Idempotency handling
- Admin alerts on failure
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.models.claims import Claim, ClaimStatus

logger = logging.getLogger(__name__)

# WhatsApp notification templates
SETTLEMENT_CONFIRMED_TEMPLATE = (
    "💰 Remboursement confirmé\n\n"
    "Votre remboursement a été effectué.\n"
    "Montant: {amount:,.0f} FCFA\n"
    "Référence: {ref}\n\n"
    "Vérifiez votre compte mobile money."
)

SETTLEMENT_FAILED_TEMPLATE = (
    "⚠️ Paiement en attente\n\n"
    "Votre remboursement rencontre un problème technique.\n"
    "Référence: {ref}\n\n"
    "Notre équipe vous contactera sous 24h."
)

PHARMACY_PAYMENT_TEMPLATE = (
    "💳 Paiement reçu\n\n"
    "Vous avez reçu un paiement Wali.\n"
    "Montant: {amount:,.0f} FCFA\n"
    "Référence: {ref}\n"
    "Patient: {patient_phone}\n\n"
    "Merci pour votre confiance."
)


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,  # Add randomness to prevent thundering herd
    time_limit=180,
    soft_time_limit=150,
)
async def settle_pharmacy_claim(self, claim_id: str):
    """
    Settle a pharmacy claim via mobile money.
    
    Workflow:
    1. Get claim and verify status
    2. Check idempotency (don't pay twice!)
    3. Calculate settlement (80% after 20% deductible)
    4. Call PaymentOrchestrator
    5. Update claim with settlement reference
    6. Send notifications
    
    Args:
        claim_id: UUID of the approved claim
    """
    from app.models.base import AsyncSessionLocal
    from app.services.payment_orchestrator import PaymentOrchestrator
    
    claim_uuid = uuid.UUID(claim_id)
    logger.info(f"Starting settlement for claim {claim_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Retrieve claim
            result = await db.execute(
                select(Claim).where(Claim.id == claim_uuid)
            )
            claim = result.scalar_one_or_none()
            
            if not claim:
                logger.error(f"Claim not found for settlement: {claim_id}")
                return {"error": "Claim not found"}
            
            # 2. Idempotency check - don't pay twice!
            if claim.settlement_reference:
                logger.warning(f"Claim {claim_id} already settled: {claim.settlement_reference}")
                return {
                    "status": "already_settled",
                    "settlement_reference": claim.settlement_reference
                }
            
            if claim.status not in [ClaimStatus.APPROVED, ClaimStatus.SETTLEMENT_FAILED]:
                logger.error(f"Cannot settle claim {claim_id} with status {claim.status}")
                return {"error": f"Invalid claim status: {claim.status}"}
            
            # 3. Calculate settlement amount (80% after 20% deductible)
            settlement_amount = claim.settlement_amount
            logger.info(f"Settlement amount for claim {claim_id}: {settlement_amount} XOF")
            
            # 4. Call PaymentOrchestrator
            orchestrator = PaymentOrchestrator()
            
            try:
                # Get pharmacy details
                from app.models.pharmacy import Pharmacy
                pharmacy_result = await db.execute(
                    select(Pharmacy).where(Pharmacy.id == claim.pharmacy_id)
                )
                pharmacy = pharmacy_result.scalar_one_or_none()
                
                if not pharmacy:
                    raise ValueError(f"Pharmacy not found: {claim.pharmacy_id}")
                
                # Initiate settlement
                settlement_result = await orchestrator.settle_pharmacy(
                    pharmacy_phone=pharmacy.payment_phone or pharmacy.phone,
                    amount=float(settlement_amount),
                    reference=f"WALI-{claim.short_id}",
                    description=f"Remboursement sinistre {claim.short_id}"
                )
                
                if settlement_result["status"] == "success":
                    # 5. Update claim
                    claim.status = ClaimStatus.SETTLED
                    claim.settled_at = datetime.now(timezone.utc)
                    claim.settlement_reference = settlement_result["transaction_id"]
                    claim.settled_amount = settlement_amount
                    await db.commit()
                    
                    logger.info(f"Claim {claim_id} settled successfully: {settlement_result['transaction_id']}")
                    
                    # 6. Send notifications
                    await _send_pharmacy_notification(
                        pharmacy.phone,
                        settlement_amount,
                        settlement_result["transaction_id"],
                        claim.artisan_phone
                    )
                    
                    await _send_artisan_settlement_notification(
                        claim.artisan_phone,
                        settlement_amount,
                        claim.short_id
                    )
                    
                    return {
                        "status": "settled",
                        "settlement_reference": settlement_result["transaction_id"],
                        "amount": float(settlement_amount)
                    }
                
                else:
                    # Payment failed - will retry
                    raise Exception(f"Payment failed: {settlement_result.get('error', 'Unknown error')}")
                    
            except Exception as payment_error:
                logger.error(f"Payment error for claim {claim_id}: {payment_error}")
                
                # Update status to failed temporarily
                claim.status = ClaimStatus.SETTLEMENT_FAILED
                await db.commit()
                
                # Retry with exponential backoff
                if self.request.retries < 5:
                    retry_delay = 30 * (2 ** self.request.retries)
                    logger.info(f"Retrying settlement for claim {claim_id} in {retry_delay}s (attempt {self.request.retries + 1}/5)")
                    raise self.retry(exc=payment_error, countdown=retry_delay)
                else:
                    # Max retries exceeded
                    logger.critical(f"SETTLEMENT_FAILED_PERMANENTLY|claim_id={claim_id}|error={payment_error}")
                    await _alert_admin_settlement_failure(claim, str(payment_error))
                    
                    # Notify artisan
                    await _send_whatsapp_notification(
                        claim.artisan_phone,
                        SETTLEMENT_FAILED_TEMPLATE.format(ref=claim.short_id)
                    )
                    
                    return {
                        "status": "failed",
                        "error": str(payment_error),
                        "retries_exhausted": True
                    }
                    
        except SoftTimeLimitExceeded:
            logger.error(f"Soft time limit exceeded for settlement {claim_id}")
            # Alert admin
            try:
                result = await db.execute(
                    select(Claim).where(Claim.id == claim_uuid)
                )
                claim = result.scalar_one_or_none()
                if claim:
                    await _alert_admin_settlement_failure(claim, "Timeout")
            except:
                pass
            raise
            
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for claim {claim_id}")
            # Final failure handling
            try:
                result = await db.execute(
                    select(Claim).where(Claim.id == claim_uuid)
                )
                claim = result.scalar_one_or_none()
                if claim:
                    claim.status = ClaimStatus.SETTLEMENT_FAILED
                    await db.commit()
                    await _alert_admin_settlement_failure(claim, "Max retries exceeded")
            except:
                pass
            
            return {"status": "failed", "error": "Max retries exceeded"}
            
        except Exception as e:
            logger.exception(f"Unexpected error settling claim {claim_id}: {e}")
            await db.rollback()
            raise


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
)
async def retry_failed_settlements(self):
    """
    Periodic task to retry failed settlements.
    
    Runs every hour to retry claims in SETTLEMENT_FAILED status.
    """
    from app.models.base import AsyncSessionLocal
    
    logger.info("Starting retry of failed settlements")
    
    async with AsyncSessionLocal() as db:
        try:
            # Find failed settlements from last 24 hours
            one_day_ago = datetime.now(timezone.utc) - __import__('datetime').timedelta(hours=24)
            
            result = await db.execute(
                select(Claim).where(
                    Claim.status == ClaimStatus.SETTLEMENT_FAILED,
                    Claim.processed_at >= one_day_ago
                )
            )
            failed_claims = result.scalars().all()
            
            logger.info(f"Found {len(failed_claims)} failed settlements to retry")
            
            for claim in failed_claims:
                logger.info(f"Queueing retry for claim {claim.id}")
                settle_pharmacy_claim.delay(str(claim.id))
            
            return {
                "retries_queued": len(failed_claims)
            }
            
        except Exception as e:
            logger.error(f"Error retrying failed settlements: {e}")
            raise


async def _send_pharmacy_notification(
    pharmacy_phone: str,
    amount: Decimal,
    reference: str,
    patient_phone: str
):
    """Send WhatsApp notification to pharmacy."""
    try:
        message = PHARMACY_PAYMENT_TEMPLATE.format(
            amount=amount,
            ref=reference,
            patient_phone=patient_phone[-8:]  # Mask full number
        )
        # TODO: Implement actual WhatsApp API call
        logger.info(f"WhatsApp to pharmacy {pharmacy_phone}: {message[:100]}...")
    except Exception as e:
        logger.error(f"Failed to send pharmacy notification: {e}")


async def _send_artisan_settlement_notification(
    artisan_phone: str,
    amount: Decimal,
    short_id: str
):
    """Send WhatsApp notification to artisan."""
    try:
        message = SETTLEMENT_CONFIRMED_TEMPLATE.format(
            amount=amount,
            ref=short_id
        )
        # TODO: Implement actual WhatsApp API call
        logger.info(f"WhatsApp to artisan {artisan_phone}: {message[:100]}...")
    except Exception as e:
        logger.error(f"Failed to send artisan notification: {e}")


async def _send_whatsapp_notification(phone: str, message: str):
    """Send WhatsApp notification."""
    try:
        # TODO: Implement actual WhatsApp API call
        logger.info(f"WhatsApp to {phone}: {message[:100]}...")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp notification: {e}")


async def _alert_admin_settlement_failure(claim: Claim, error: str):
    """Alert admin on settlement failure."""
    logger.critical(
        f"SETTLEMENT_FAILURE|"
        f"claim_id={claim.id}|"
        f"amount={claim.amount}|"
        f"phone={claim.artisan_phone}|"
        f"error={error}|"
        f"MANUAL_RECONCILIATION_REQUIRED"
    )
    # TODO: Send actual alert (SMS/email/Slack)
    # This is revenue-critical - admin must be notified immediately


# Export tasks
__all__ = ["settle_pharmacy_claim", "retry_failed_settlements"]
