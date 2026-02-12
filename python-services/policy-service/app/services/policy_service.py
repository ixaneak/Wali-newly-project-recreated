"""
Enrollment Service (was: PolicyService)

Manages artisan enrollment into partner insurer products.
Wali facilitates enrollment; the partner insurer owns the coverage.
We do NOT calculate premiums, set rates, or perform underwriting.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import uuid
import logging
import requests


from app.models.policy import (
    CoverageSubscription, SubscriptionStatus, PaymentFrequency,
)
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _calculate_next_payment_date(
    frequency: PaymentFrequency,
    from_date: Optional[datetime] = None,
) -> datetime:
    """Calculate next payment date based on frequency."""
    base = from_date or datetime.now()
    if frequency == PaymentFrequency.DAILY:
        return base + timedelta(days=1)
    elif frequency == PaymentFrequency.WEEKLY:
        return base + timedelta(weeks=1)
    else:  # MONTHLY
        return base + timedelta(days=30)


class EnrollmentService:
    """
    Service for managing artisan enrollments with partner insurers.

    IMPORTANT: Wali does NOT set premiums or calculate rates.
    The partner_quoted_amount comes from the partner insurer's
    product catalog, not from any internal calculation.
    """

    @staticmethod
    def create_enrollment(
        db: Session,
        user_id: str,
        partner_id: str,
            partner_product_id: str,
            partner_product_config: dict,
            payment_frequency: PaymentFrequency,
            is_test: bool = False,
        ) -> CoverageSubscription:
        """
        Enroll artisan in partner insurer's coverage product.

        Args:
            db: Database session
            user_id: Artisan's user ID
            partner_id: Partner insurer (e.g. "NSIA")
            partner_product_id: Product code from partner catalog
            partner_product_config: Coverage details (must include coverage_amount)
            payment_frequency: How often artisan pays
            is_test: If True, bypass partner API and create ACTIVE policy immediately

        Returns:
            Created CoverageSubscription
        """
        partner_quoted_amount = 0
        subscription_status = SubscriptionStatus.PENDING
        start_date = None
        end_date = None
        last_payment_date = None
        next_payment_date = None

        if is_test:
            # TEST MODE: Bypass partner API, mock successful quote and payment
            logger.info("TEST MODE: Creating active policy for user %s", user_id)
            partner_quoted_amount = 1000  # Mock amount
            subscription_status = SubscriptionStatus.ACTIVE
            start_date = datetime.now()
            last_payment_date = datetime.now()
            next_payment_date = _calculate_next_payment_date(payment_frequency, start_date)
            # End date could be set based on frequency or default strict duration, 
            # but usually it's open-ended until cancelled or expired.
            # Let's set it to None for indefinitely active, or +1 year/month.
        else:
            # 1. Fetch Quote from Partner (SaaS Compliance)
            # We generally shouldn't hardcode localhost, but for this Mock Sprint it is required.
            # In prod, this would use partner.api_url from DB.
            try:
                # Extract coverage amount from config or default to 0
                coverage_amt = partner_product_config.get("coverage_amount", 1000000)
                
                response = requests.post(
                    "http://localhost:8008/v1/quotes",
                    json={
                        "product_code": partner_product_id,
                        "coverage_amount": coverage_amt
                    },
                    timeout=5
                )
                response.raise_for_status()
                quote_data = response.json()
                
                # The PARTNER sets the price. We just record it.
                partner_quoted_amount = quote_data["premium_amount"]
                partner_quote_id = quote_data["quote_id"]
                
                logger.info("Fetched quote from partner: %s = %d XOF", partner_quote_id, partner_quoted_amount)
                
            except Exception as e:
                logger.error("Failed to fetch quote from partner: %s", e)
                raise ValueError("Could not obtain pricing from partner insurer. Please try again.")

        subscription_number = f"SUB-{str(uuid.uuid4())[:8].upper()}"

        subscription = CoverageSubscription(
            user_id=user_id,
            subscription_number=subscription_number,
            partner_id=partner_id,
            partner_product_id=partner_product_id,
            partner_product_config=partner_product_config,
            partner_quoted_amount=partner_quoted_amount,
            # partner_quote_id=partner_quote_id,  # TODO: Add column to DB? For now just log it.
            payment_frequency=payment_frequency,
            status=subscription_status,
            start_date=start_date,
            last_payment_date=last_payment_date,
            next_payment_date=next_payment_date,
            end_date=end_date,
        )

        try:
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            logger.info(
                "Enrollment %s created for user %s with partner %s (product: %s, amount: %d)",
                subscription_number, user_id, partner_id, partner_product_id, partner_quoted_amount,
            )
            return subscription
        except Exception as e:
            db.rollback()
            logger.error("Failed to create enrollment: %s", e)
            raise ValueError(f"Failed to create enrollment: {e}")

    @staticmethod
    def confirm_enrollment(
        db: Session,
        subscription_id: str,
        transaction_ref: str,
    ) -> CoverageSubscription:
        """
        Confirm enrollment after payment has been ROUTED to partner.

        Note: This is triggered when the partner confirms receipt of
        the artisan's payment, not by Wali receiving the payment.
        """
        sub = db.query(CoverageSubscription).filter(
            CoverageSubscription.id == subscription_id
        ).first()
        if not sub:
            raise ValueError("Subscription not found")

        sub.status = SubscriptionStatus.ACTIVE
        sub.mobile_money_ref = transaction_ref
        sub.start_date = datetime.now()
        sub.last_payment_date = datetime.now()
        sub.next_payment_date = _calculate_next_payment_date(sub.payment_frequency)

        db.commit()
        db.refresh(sub)
        logger.info("Enrollment %s confirmed (ref: %s)", sub.subscription_number, transaction_ref)
        return sub

    @staticmethod
    def get_user_enrollments(
        db: Session,
        user_id: str,
        status: Optional[SubscriptionStatus] = None,
    ):
        """Get all enrollments for an artisan."""
        query = db.query(CoverageSubscription).filter(
            CoverageSubscription.user_id == user_id
        )
        if status:
            query = query.filter(CoverageSubscription.status == status)
        return query.order_by(CoverageSubscription.created_at.desc()).all()

    @staticmethod
    def get_enrollment(db: Session, subscription_id: str) -> Optional[CoverageSubscription]:
        """Get a single enrollment by ID."""
        return db.query(CoverageSubscription).filter(
            CoverageSubscription.id == subscription_id
        ).first()

    @staticmethod
    def record_payment_routing(
        db: Session,
        subscription_id: str,
        transaction_ref: str,
    ) -> CoverageSubscription:
        """Update enrollment after payment has been routed to partner."""
        sub = db.query(CoverageSubscription).filter(
            CoverageSubscription.id == subscription_id
        ).first()
        if not sub:
            raise ValueError("Subscription not found")

        sub.last_payment_date = datetime.now()
        sub.next_payment_date = _calculate_next_payment_date(
            sub.payment_frequency, from_date=datetime.now()
        )
        sub.mobile_money_ref = transaction_ref

        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def cancel_enrollment(
        db: Session,
        subscription_id: str,
        reason: str,
    ) -> CoverageSubscription:
        """Cancel an enrollment."""
        sub = db.query(CoverageSubscription).filter(
            CoverageSubscription.id == subscription_id
        ).first()
        if not sub:
            raise ValueError("Subscription not found")

        sub.status = SubscriptionStatus.CANCELLED
        sub.cancellation_reason = reason
        sub.end_date = datetime.now()

        db.commit()
        db.refresh(sub)
        logger.info("Enrollment %s cancelled: %s", sub.subscription_number, reason)
        return sub


# Backward-compatible alias
PolicyService = EnrollmentService
