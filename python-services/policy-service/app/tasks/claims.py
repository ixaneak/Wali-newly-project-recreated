"""
Celery Tasks for Claims Processing.

Async workers for:
- Claim submission processing
- Image forensics analysis
- Status updates
- WhatsApp notifications
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiohttp
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app, get_task_retry_config
from app.models.claims import Claim, ClaimStatus, DataTransferLog, FraudLog
from app.services.fraud.image_forensics import ImageDownloader, ImageForensicsService
from app.services.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)

# WhatsApp notification templates (simplified)
CLAIM_APPROVED_TEMPLATE = (
    "✅ Sinistre approuvé\n\n"
    "Votre demande a été approuvée.\n"
    "Montant: {amount:,.0f} FCFA\n"
    "Référence: {ref}\n\n"
    "Le paiement est en cours de traitement."
)

CLAIM_FRAUD_REVIEW_TEMPLATE = (
    "⏳ Vérification en cours\n\n"
    "Votre demande est en cours de vérification administrative.\n"
    "Référence: {ref}\n\n"
    "Délai estimé: 24-48 heures."
)

CLAIM_REJECTED_TEMPLATE = (
    "❌ Sinistre refusé\n\n"
    "Votre demande a été refusée.\n"
    "Raison: {reason}\n\n"
    "Pour contester: contactez le support au 130"
)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    time_limit=300,
    soft_time_limit=240,
)
async def process_claim_submission(self, claim_id: str):
    """
    Process a new claim submission.
    
    Workflow:
    1. Retrieve claim from DB
    2. Download image from B2
    3. Run fraud analysis
    4. Update claim status
    5. If approved, trigger settlement
    6. Send WhatsApp notification
    
    Args:
        claim_id: UUID of the claim to process
    """
    from app.models.base import AsyncSessionLocal
    
    claim_uuid = uuid.UUID(claim_id)
    logger.info(f"Processing claim submission: {claim_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Retrieve claim
            result = await db.execute(
                select(Claim).where(Claim.id == claim_uuid)
            )
            claim = result.scalar_one_or_none()
            
            if not claim:
                logger.error(f"Claim not found: {claim_id}")
                return {"error": "Claim not found"}
            
            if claim.status != ClaimStatus.SUBMITTED:
                logger.warning(f"Claim {claim_id} already processed (status: {claim.status})")
                return {"status": "already_processed"}
            
            # Update status to processing
            claim.status = ClaimStatus.PROCESSING
            await db.commit()
            
            # 2. Download image from Backblaze B2
            try:
                downloader = ImageDownloader(timeout=30)
                image_bytes = await downloader.download(claim.image_url)
                
                # Log data transfer (ARTCI compliance)
                await _log_data_transfer(db, claim_id, "image_download", "USA/Backblaze")
                
            except aiohttp.ClientError as e:
                logger.error(f"Failed to download image for claim {claim_id}: {e}")
                claim.status = ClaimStatus.SUBMITTED  # Reset for retry
                await db.commit()
                
                # Retry with exponential backoff
                if self.request.retries < 3:
                    logger.info(f"Retrying claim {claim_id} in {60 * (2 ** self.request.retries)}s")
                    raise self.retry(countdown=60 * (2 ** self.request.retries))
                else:
                    # Max retries exceeded - flag for manual review
                    claim.status = ClaimStatus.FRAUD_REVIEW
                    claim.fraud_flags.append("IMAGE_DOWNLOAD_FAILED")
                    claim.reviewer_notes = f"Failed to download image after 3 retries: {str(e)}"
                    await db.commit()
                    return {"status": "fraud_review", "reason": "image_download_failed"}
            
            # 3. Run fraud analysis
            context = {
                "claim_id": claim_id,
                "artisan_phone": claim.artisan_phone,
                "claim_type": claim.claim_type.value,
                "pharmacy_id": str(claim.pharmacy_id) if claim.pharmacy_id else None,
                "submitted_at": claim.submitted_at,
                "device_fingerprint": claim.device_fingerprint,
            }
            
            forensics_service = ImageForensicsService(db)
            fraud_report = await forensics_service.analyze(image_bytes, context)
            
            # 4. Update claim with fraud results
            claim.fraud_score = fraud_report.risk_score
            claim.fraud_flags = fraud_report.flags
            claim.image_hash = fraud_report.perceptual_hash
            claim.exif_gps = fraud_report.gps_coordinates
            claim.exif_timestamp = fraud_report.exif_timestamp
            
            if fraud_report.is_suspicious:
                claim.status = ClaimStatus.FRAUD_REVIEW
                logger.warning(f"Claim {claim_id} flagged for fraud review (score: {fraud_report.risk_score:.2f})")
                
                # Send fraud review notification
                await _send_whatsapp_notification(
                    claim.artisan_phone,
                    CLAIM_FRAUD_REVIEW_TEMPLATE.format(ref=claim.short_id)
                )
                
                # Alert admin
                await _alert_admin_fraud_review(claim)
                
            else:
                claim.status = ClaimStatus.APPROVED
                logger.info(f"Claim {claim_id} approved (score: {fraud_report.risk_score:.2f})")
                
                # Send approval notification
                await _send_whatsapp_notification(
                    claim.artisan_phone,
                    CLAIM_APPROVED_TEMPLATE.format(
                        amount=claim.amount,
                        ref=claim.short_id
                    )
                )
                
                # 5. Trigger settlement for pharmacy claims
                if claim.claim_type.value == "pharmacy":
                    from app.tasks.payments import settle_pharmacy_claim
                    settle_pharmacy_claim.delay(claim_id)
                    logger.info(f"Queued settlement for claim {claim_id}")
            
            claim.processed_at = datetime.now(timezone.utc)
            await db.commit()
            
            return {
                "status": claim.status.value,
                "fraud_score": fraud_report.risk_score,
                "flags": fraud_report.flags,
            }
            
        except SoftTimeLimitExceeded:
            logger.error(f"Soft time limit exceeded for claim {claim_id}")
            # Update claim status and alert
            try:
                claim.status = ClaimStatus.FRAUD_REVIEW
                claim.fraud_flags.append("PROCESSING_TIMEOUT")
                claim.reviewer_notes = "Processing timed out - manual review required"
                await db.commit()
            except:
                await db.rollback()
            raise
            
        except Exception as e:
            logger.exception(f"Error processing claim {claim_id}: {e}")
            await db.rollback()
            
            # Retry logic
            if self.request.retries < 3:
                raise self.retry(exc=e)
            else:
                # Max retries - flag for manual review
                try:
                    result = await db.execute(
                        select(Claim).where(Claim.id == claim_uuid)
                    )
                    claim = result.scalar_one_or_none()
                    if claim:
                        claim.status = ClaimStatus.FRAUD_REVIEW
                        claim.fraud_flags.append("PROCESSING_ERROR")
                        claim.reviewer_notes = f"Processing failed after 3 retries: {str(e)}"
                        await db.commit()
                except:
                    pass
                
                return {"status": "error", "message": str(e)}


@celery_app.task(
    bind=True,
    max_retries=0,  # No retries - CPU intensive, fail fast
    time_limit=120,
)
async def analyze_image_fraud(self, claim_id: str, image_url: str, context: dict):
    """
    Standalone task for fraud analysis.
    
    Used when fraud analysis needs to be re-run or done separately.
    No retries - if it fails, alert admin.
    """
    from app.models.base import AsyncSessionLocal
    
    logger.info(f"Running standalone fraud analysis for claim {claim_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Download image
            downloader = ImageDownloader(timeout=30)
            image_bytes = await downloader.download(image_url)
            
            # Analyze
            forensics_service = ImageForensicsService(db)
            report = await forensics_service.analyze(image_bytes, context)
            
            return {
                "claim_id": claim_id,
                "risk_score": report.risk_score,
                "is_suspicious": report.is_suspicious,
                "flags": report.flags,
            }
            
        except Exception as e:
            logger.exception(f"Fraud analysis failed for claim {claim_id}: {e}")
            # Alert admin - fraud system failure
            await _alert_admin_system_failure("fraud_analysis", claim_id, str(e))
            raise


async def _log_data_transfer(
    db: AsyncSession,
    claim_id: str,
    transfer_type: str,
    destination: str
):
    """
    Log cross-border data transfer for ARTCI compliance.
    
    Law 2013-450 requires logging all transfers outside Côte d'Ivoire.
    """
    try:
        log = DataTransferLog(
            claim_id=uuid.UUID(claim_id) if claim_id else None,
            transfer_type=transfer_type,
            destination=destination,
            data_type="image",
            legal_basis="contract_performance"
        )
        db.add(log)
        await db.commit()
    except Exception as e:
        logger.error(f"Error logging data transfer: {e}")
        await db.rollback()


async def _send_whatsapp_notification(phone: str, message: str):
    """
    Send WhatsApp notification to artisan.
    
    In production, this would call the WhatsApp Business API.
    For now, we log the message.
    """
    try:
        # TODO: Implement actual WhatsApp API call
        # client = WhatsAppClient()
        # await client.send_message(phone, message)
        logger.info(f"WhatsApp to {phone}: {message[:100]}...")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp notification: {e}")


async def _alert_admin_fraud_review(claim: Claim):
    """Alert admin when claim needs fraud review."""
    logger.critical(
        f"FRAUD_REVIEW_REQUIRED|"
        f"claim_id={claim.id}|"
        f"phone={claim.artisan_phone}|"
        f"score={claim.fraud_score:.2f}|"
        f"flags={claim.fraud_flags}"
    )
    # TODO: Send actual alert (SMS/email/Slack)


async def _alert_admin_system_failure(component: str, claim_id: str, error: str):
    """Alert admin on system failure."""
    logger.critical(
        f"SYSTEM_FAILURE|"
        f"component={component}|"
        f"claim_id={claim_id}|"
        f"error={error}"
    )
    # TODO: Send actual alert


# Import tasks to register them
__all__ = ["process_claim_submission", "analyze_image_fraud"]
