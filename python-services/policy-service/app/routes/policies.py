"""
Enrollment API Routes (was: policies.py)

Manages artisan enrollment into partner insurer products.
Wali provides the technology; the partner insurer owns the coverage.

All endpoints use /partners/{partner_id}/enrollments pattern
to emphasize B2B SaaS architecture.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.core.security_middleware_v2 import verify_jwt, verify_admin
from app.models.policy import SubscriptionStatus, PaymentFrequency
from app.services.policy_service import EnrollmentService
from app.services import sar_service
from app.core.rate_limit import limiter

router = APIRouter(prefix="/api/v1/partners", tags=["enrollments"])
logger = logging.getLogger(__name__)


# ==================== Pydantic Schemas ====================

class EnrollmentCreateRequest(BaseModel):
    """Request to enroll artisan in partner's coverage product."""
    user_id: str
    partner_product_id: str = Field(..., description="Product code from partner catalog (e.g. NSIA-HEALTH-01)")
    partner_product_config: dict = Field(..., description="Coverage details defined by partner insurer")
    # Note: partner_quoted_amount field removed - pricing determined by partner insurer
    payment_frequency: PaymentFrequency
    is_test: bool = False


class EnrollmentConfirmRequest(BaseModel):
    """Confirm enrollment after payment routed to partner."""
    transaction_ref: str


class PaymentRoutingRequest(BaseModel):
    """Record payment routing to partner."""
    transaction_ref: str


class EnrollmentCancelRequest(BaseModel):
    """Cancel an enrollment."""
    reason: str


class EnrollmentResponse(BaseModel):
    """Enrollment response."""
    id: str
    user_id: str
    subscription_number: str
    partner_id: str
    partner_product_id: str
    partner_product_config: dict
    partner_quoted_amount: int
    payment_frequency: str
    status: str
    mobile_money_ref: Optional[str] = None
    last_payment_date: Optional[str] = None
    next_payment_date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # QR Feature
    qr_token: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== Routes ====================

@router.post(
    "/{partner_id}/enrollments",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
def create_enrollment(
    partner_id: str,
    request: Request,
    enrollment_request: EnrollmentCreateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """
    Enroll artisan in partner insurer's coverage product.

    The product and pricing come from the partner insurer,
    NOT from Wali. Wali provides the technology layer only.
    """
    # Quick mock bypass for test/demo mode — avoids DB dependency
    if enrollment_request.is_test:
        # SECURITY: Test mode enrollment MUST ONLY be allowed in development.
        # This bypasses the insurer API and DB persistence.
        import os
        if os.getenv('ENV') != 'development':
            logger.warning(f"Blocking test enrollment request in {os.getenv('ENV')} environment")
            raise HTTPException(status_code=403, detail="Test mode disabled")

        from datetime import datetime, timedelta
        import uuid
        mock_id = str(uuid.uuid4())
        return {
            "id": mock_id,
            "user_id": enrollment_request.user_id,
            "subscription_number": f"SUB-TEST-{mock_id[:8].upper()}",
            "partner_id": partner_id,
            "partner_product_id": enrollment_request.partner_product_id,
            "partner_product_config": enrollment_request.partner_product_config,
            "partner_quoted_amount": 1000,
            "payment_frequency": enrollment_request.payment_frequency.value if hasattr(enrollment_request.payment_frequency, 'value') else str(enrollment_request.payment_frequency),
            "status": "active",
            "mobile_money_ref": None,
            "last_payment_date": datetime.utcnow().isoformat(),
            "next_payment_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "start_date": datetime.utcnow().isoformat(),
            "end_date": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    try:
        subscription = EnrollmentService.create_enrollment(
            db=db,
            user_id=enrollment_request.user_id,
            partner_id=partner_id,
            partner_product_id=enrollment_request.partner_product_id,
            partner_product_config=enrollment_request.partner_product_config,
            # Note: partner_quoted_amount removed per SaaS compliance - partner sets pricing
            payment_frequency=enrollment_request.payment_frequency,
            is_test=enrollment_request.is_test,
        )

        # ── SAR Detection (non-blocking) ────────────────────────
        # Run risk scoring on every new enrollment. Never block
        # legitimate users — alert compliance team for critical hits.
        try:
            amount = getattr(subscription, 'partner_quoted_amount', 0) or 0
            result = sar_service.score_transaction(
                db=db,
                user_id=enrollment_request.user_id,
                amount=amount,
                policy_id=getattr(subscription, 'id', None),
            )

            if result["rules_fired"] > 0:
                risk_event = sar_service.create_risk_event(
                    db=db,
                    event_type="policy_creation",
                    severity=result["severity"],
                    risk_score=result["risk_score"],
                    triggered_rules=result["triggered_rules"],
                    user_id=enrollment_request.user_id,
                    policy_id=getattr(subscription, 'id', None),
                    raw_data={
                        "amount": amount,
                        "partner_id": partner_id,
                        "product_id": enrollment_request.partner_product_id,
                    },
                )
                if result["severity"] == "critical":
                    logger.critical(
                        f"🚨 SAR ALERT: Critical risk on enrollment "
                        f"{getattr(subscription, 'id', '?')} — "
                        f"score={result['risk_score']}, "
                        f"rules={[r.get('rule') for r in result['triggered_rules']]}"
                    )
        except Exception as sar_err:
            # Never let SAR analysis break the enrollment flow
            logger.error(f"SAR analysis failed (non-blocking): {sar_err}")
        # ── End SAR Detection ───────────────────────────────────

        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating enrollment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{partner_id}/enrollments/{subscription_id}", response_model=EnrollmentResponse)
def get_enrollment(
    partner_id: str,
    subscription_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """Get a specific enrollment."""
    sub = EnrollmentService.get_enrollment(db, subscription_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    return sub.to_dict()


@router.get("/{partner_id}/enrollments/user/{user_id}", response_model=List[EnrollmentResponse])
def get_user_enrollments(
    partner_id: str,
    user_id: str,
    status_filter: Optional[SubscriptionStatus] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """Get all enrollments for an artisan."""
    subs = EnrollmentService.get_user_enrollments(db, user_id, status_filter)
    return [s.to_dict() for s in subs]


@router.post("/{partner_id}/enrollments/{subscription_id}/confirm", response_model=EnrollmentResponse)
def confirm_enrollment(
    partner_id: str,
    subscription_id: str,
    request: EnrollmentConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    Confirm enrollment after payment has been routed to partner insurer.

    This endpoint is called when the partner confirms receipt of payment.
    """
    try:
        sub = EnrollmentService.confirm_enrollment(db, subscription_id, request.transaction_ref)
        return sub.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{partner_id}/enrollments/{subscription_id}/payment", response_model=EnrollmentResponse)
def record_payment_routing(
    partner_id: str,
    subscription_id: str,
    request: PaymentRoutingRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """Update enrollment after payment routed to partner."""
    try:
        sub = EnrollmentService.record_payment_routing(db, subscription_id, request.transaction_ref)
        return sub.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{partner_id}/enrollments/{subscription_id}/cancel", response_model=EnrollmentResponse)
def cancel_enrollment(
    partner_id: str,
    subscription_id: str,
    request: EnrollmentCancelRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """Cancel an enrollment."""
    try:
        sub = EnrollmentService.cancel_enrollment(db, subscription_id, request.reason)
        return sub.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{partner_id}/enrollments", response_model=List[EnrollmentResponse])
def list_partner_enrollments(
    partner_id: str,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[SubscriptionStatus] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """List all enrollments for a partner (admin only)."""
    from app.models.policy import CoverageSubscription

    query = db.query(CoverageSubscription).filter(
        CoverageSubscription.partner_id == partner_id
    )
    if status_filter:
        query = query.filter(CoverageSubscription.status == status_filter)

    subs = query.offset(skip).limit(limit).all()
    return [s.to_dict() for s in subs]


@router.get("/{partner_id}/enrollments/{subscription_id}/certificate")
def get_enrollment_certificate(
    partner_id: str,
    subscription_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """Generate enrollment confirmation document."""
    from fastapi.responses import Response
    from app.services.pdf_service import generate_policy_certificate

    sub = EnrollmentService.get_enrollment(db, subscription_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    pdf_bytes = generate_policy_certificate(sub.to_dict())

    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
        },
    )

# ==================== User Policy Routes (Legacy/Convenience) ====================

# Router initialized
policies_router = APIRouter(prefix="/api/v1/policies", tags=["policies"])

@policies_router.get("/my-policies", response_model=List[EnrollmentResponse])
def get_my_policies(
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """Get all policies for the current logged-in user."""
    user_id = user["user_id"]
    subs = EnrollmentService.get_user_enrollments(db, user_id)
    return [s.to_dict() for s in subs]
