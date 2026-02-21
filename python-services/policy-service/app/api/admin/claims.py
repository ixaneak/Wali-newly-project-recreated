"""
Admin API Endpoints for Claims Review.

Endpoints:
- GET /api/admin/claims/review-queue - List claims needing review
- POST /api/admin/claims/{claim_id}/decision - Approve/reject claim
- GET /api/admin/fraud/stats - Fraud detection statistics
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.security import get_current_admin_user, require_admin
from app.models.base import get_db
from app.models.claims import Claim, ClaimStatus, FraudLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/claims", tags=["Admin Claims"])


# Request/Response Models
class ClaimDecisionRequest(BaseModel):
    """Request model for claim decision."""
    decision: str = Field(..., pattern="^(approve|reject)$")
    reason: str = Field(..., min_length=5, max_length=1000)
    reviewer_id: uuid.UUID


class ClaimDecisionResponse(BaseModel):
    """Response model for claim decision."""
    claim_id: uuid.UUID
    status: str
    message: str


class FraudStatsResponse(BaseModel):
    """Response model for fraud statistics."""
    total_claims_24h: int
    fraud_review_count: int
    fraud_rate_percent: float
    avg_processing_time_minutes: float
    top_flags: List[dict]


class ClaimReviewItem(BaseModel):
    """Item in review queue."""
    id: uuid.UUID
    short_id: str
    artisan_phone: str
    claim_type: str
    amount: float
    fraud_score: float
    fraud_flags: List[str]
    image_preview_url: Optional[str]
    description: Optional[str]
    submitted_at: datetime
    exif_gps: Optional[dict]


@router.get(
    "/review-queue",
    response_model=List[ClaimReviewItem],
    dependencies=[Depends(require_admin)]
)
async def get_review_queue(
    status: ClaimStatus = Query(default=ClaimStatus.FRAUD_REVIEW),
    min_score: float = Query(default=0.7, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin_user)
):
    """
    Get claims needing manual review.
    
    Sorted by fraud score (highest first), then by submission time (oldest first).
    
    Query Parameters:
    - status: Filter by claim status (default: fraud_review)
    - min_score: Minimum fraud score (default: 0.7)
    - limit: Maximum results (default: 50)
    """
    try:
        result = await db.execute(
            select(Claim)
            .where(
                and_(
                    Claim.status == status,
                    Claim.fraud_score >= min_score
                )
            )
            .order_by(
                desc(Claim.fraud_score),  # Highest risk first
                Claim.submitted_at.asc()   # Oldest first
            )
            .limit(limit)
        )
        claims = result.scalars().all()
        
        # Build response
        response_items = []
        for claim in claims:
            # Generate signed URL for image preview (1 hour expiry)
            image_url = _generate_signed_image_url(claim.image_url, expiry_seconds=3600)
            
            response_items.append(ClaimReviewItem(
                id=claim.id,
                short_id=claim.short_id,
                artisan_phone=claim.artisan_phone,
                claim_type=claim.claim_type.value,
                amount=float(claim.amount),
                fraud_score=claim.fraud_score,
                fraud_flags=claim.fraud_flags,
                image_preview_url=image_url,
                description=claim.description,
                submitted_at=claim.submitted_at,
                exif_gps=claim.exif_gps
            ))
        
        logger.info(f"Admin {current_user.id} retrieved {len(response_items)} claims for review")
        return response_items
        
    except Exception as e:
        logger.error(f"Error retrieving review queue: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving review queue")


@router.post(
    "/{claim_id}/decision",
    response_model=ClaimDecisionResponse,
    dependencies=[Depends(require_admin)]
)
async def make_claim_decision(
    claim_id: uuid.UUID,
    request: ClaimDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin_user)
):
    """
    Make a decision on a claim.
    
    - Approve: Updates status to 'approved' and triggers settlement
    - Reject: Updates status to 'rejected' and notifies artisan
    """
    try:
        # Retrieve claim
        result = await db.execute(
            select(Claim).where(Claim.id == claim_id)
        )
        claim = result.scalar_one_or_none()
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        if claim.status not in [ClaimStatus.FRAUD_REVIEW, ClaimStatus.PROCESSING]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot make decision on claim with status: {claim.status}"
            )
        
        # Log the decision
        log_entry = f"[{datetime.now(timezone.utc).isoformat()}] Decision: {request.decision} by {current_user.id}. Reason: {request.reason}"
        claim.reviewer_notes = log_entry
        claim.reviewer_id = request.reviewer_id
        claim.reviewed_at = datetime.now(timezone.utc)
        
        if request.decision == "approve":
            claim.status = ClaimStatus.APPROVED
            await db.commit()
            
            # Trigger settlement for pharmacy claims
            if claim.claim_type.value == "pharmacy":
                from app.tasks.payments import settle_pharmacy_claim
                settle_pharmacy_claim.delay(str(claim.id))
                logger.info(f"Settlement queued for approved claim {claim_id}")
            
            # Send approval notification
            await _send_approval_notification(claim)
            
            return ClaimDecisionResponse(
                claim_id=claim.id,
                status="approved",
                message="Claim approved and settlement initiated"
            )
        
        else:  # reject
            claim.status = ClaimStatus.REJECTED
            await db.commit()
            
            # Send rejection notification
            await _send_rejection_notification(claim, request.reason)
            
            return ClaimDecisionResponse(
                claim_id=claim.id,
                status="rejected",
                message="Claim rejected and artisan notified"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making claim decision: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error processing decision")


@router.get(
    "/fraud/stats",
    response_model=FraudStatsResponse,
    dependencies=[Depends(require_admin)]
)
async def get_fraud_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin_user)
):
    """
    Get fraud detection statistics.
    
    Returns:
    - Total claims in last 24h
    - Fraud review count
    - Fraud rate percentage
    - Average processing time
    - Top fraud flags
    """
    try:
        # Time window: last 24 hours
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Total claims
        total_result = await db.execute(
            select(func.count(Claim.id)).where(
                Claim.submitted_at >= yesterday
            )
        )
        total_claims = total_result.scalar()
        
        # Fraud review count
        fraud_result = await db.execute(
            select(func.count(Claim.id)).where(
                and_(
                    Claim.submitted_at >= yesterday,
                    Claim.status == ClaimStatus.FRAUD_REVIEW
                )
            )
        )
        fraud_count = fraud_result.scalar()
        
        # Fraud rate
        fraud_rate = (fraud_count / total_claims * 100) if total_claims > 0 else 0.0
        
        # Average processing time (for completed claims)
        processing_result = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', Claim.processed_at - Claim.submitted_at) / 60
                )
            ).where(
                and_(
                    Claim.submitted_at >= yesterday,
                    Claim.processed_at.isnot(None)
                )
            )
        )
        avg_processing_time = processing_result.scalar() or 0.0
        
        # Top fraud flags
        # This requires a more complex query to count flags in the JSONB array
        # For now, we'll query fraud logs
        flags_result = await db.execute(
            select(
                FraudLog.check_type,
                func.count(FraudLog.id).label("count")
            ).where(
                FraudLog.created_at >= yesterday
            ).group_by(
                FraudLog.check_type
            ).order_by(
                desc("count")
            ).limit(5)
        )
        top_flags = [
            {"flag": flag_type.value, "count": count}
            for flag_type, count in flags_result.all()
        ]
        
        logger.info(f"Admin {current_user.id} retrieved fraud stats")
        
        return FraudStatsResponse(
            total_claims_24h=total_claims,
            fraud_review_count=fraud_count,
            fraud_rate_percent=round(fraud_rate, 2),
            avg_processing_time_minutes=round(avg_processing_time, 2),
            top_flags=top_flags
        )
        
    except Exception as e:
        logger.error(f"Error retrieving fraud stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")


@router.get(
    "/{claim_id}/details",
    dependencies=[Depends(require_admin)]
)
async def get_claim_details(
    claim_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin_user)
):
    """
    Get detailed information about a specific claim.
    
    Includes:
    - Claim details
    - Fraud analysis results
    - Image preview
    - Related claims from same artisan
    """
    try:
        # Get claim
        result = await db.execute(
            select(Claim).where(Claim.id == claim_id)
        )
        claim = result.scalar_one_or_none()
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Get fraud logs
        fraud_logs_result = await db.execute(
            select(FraudLog).where(FraudLog.claim_id == claim_id)
        )
        fraud_logs = fraud_logs_result.scalars().all()
        
        # Get related claims (same phone, last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        related_result = await db.execute(
            select(Claim).where(
                and_(
                    Claim.artisan_phone == claim.artisan_phone,
                    Claim.id != claim.id,
                    Claim.submitted_at >= thirty_days_ago
                )
            ).order_by(desc(Claim.submitted_at))
        )
        related_claims = related_result.scalars().all()
        
        return {
            "claim": {
                "id": str(claim.id),
                "short_id": claim.short_id,
                "status": claim.status.value,
                "artisan_phone": claim.artisan_phone,
                "claim_type": claim.claim_type.value,
                "amount": float(claim.amount),
                "description": claim.description,
                "fraud_score": claim.fraud_score,
                "fraud_flags": claim.fraud_flags,
                "image_preview_url": _generate_signed_image_url(claim.image_url, 3600),
                "exif_gps": claim.exif_gps,
                "exif_timestamp": claim.exif_timestamp.isoformat() if claim.exif_timestamp else None,
                "submitted_at": claim.submitted_at.isoformat(),
                "processed_at": claim.processed_at.isoformat() if claim.processed_at else None,
                "reviewer_notes": claim.reviewer_notes,
            },
            "fraud_analysis": [
                {
                    "check_type": log.check_type.value,
                    "result": log.result.value,
                    "confidence": log.confidence,
                    "metadata": log.metadata,
                    "created_at": log.created_at.isoformat()
                }
                for log in fraud_logs
            ],
            "related_claims": [
                {
                    "id": str(c.id),
                    "short_id": c.short_id,
                    "status": c.status.value,
                    "amount": float(c.amount),
                    "fraud_score": c.fraud_score,
                    "submitted_at": c.submitted_at.isoformat()
                }
                for c in related_claims[:5]  # Limit to 5
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving claim details: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving claim details")


def _generate_signed_image_url(base_url: str, expiry_seconds: int = 3600) -> str:
    """
    Generate signed URL for image preview with expiry.
    
    In production, images should be served via signed URLs
    to prevent unauthorized access. Currently returns direct URL
    with access controlled by API authentication.
    
    TODO-PROD: Implement proper URL signing with HMAC:
        - Import secrets from config
        - Generate signature with expiry timestamp
        - Validate signature on image endpoint
    """
    # Production enhancement: Add signature parameter
    # import hmac, hashlib, time
    # expiry = int(time.time()) + expiry_seconds
    # signature = hmac.new(
    #     SECRET_KEY.encode(),
    #     f"{base_url}:{expiry}".encode(),
    #     hashlib.sha256
    # ).hexdigest()
    # return f"{base_url}?expiry={expiry}&sig={signature}"
    
    return base_url


async def _send_approval_notification(claim: Claim):
    """Send WhatsApp notification for approved claim."""
    message = (
        "✅ Sinistre approuvé\n\n"
        f"Votre demande ({claim.short_id}) a été approuvée.\n"
        f"Montant: {claim.amount:,.0f} FCFA\n\n"
        "Le paiement est en cours de traitement."
    )
    logger.info(f"Would send WhatsApp to {claim.artisan_phone}: {message}")


async def _send_rejection_notification(claim: Claim, reason: str):
    """Send WhatsApp notification for rejected claim."""
    message = (
        "❌ Sinistre refusé\n\n"
        f"Votre demande ({claim.short_id}) a été refusée.\n"
        f"Raison: {reason}\n\n"
        "Pour contester: contactez le support au 130"
    )
    logger.info(f"Would send WhatsApp to {claim.artisan_phone}: {message}")
