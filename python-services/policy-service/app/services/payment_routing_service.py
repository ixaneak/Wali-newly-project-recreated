"""
Payment Routing Service

Ensures artisan premiums go DIRECTLY to the partner insurer (NSIA).
Wali NEVER touches, holds, or collects customer insurance premiums.

Money flow:
  Artisan → PayDunya/Wave/Orange → Partner Insurer (NSIA)
  Partner Insurer → Wali (monthly SaaS subscription fee — separate flow)
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.partner import Partner, PartnerApiConfig

logger = logging.getLogger(__name__)


class PaymentRoutingService:
    """
    Routes artisan payments DIRECTLY to partner insurer.
    Wali only provides the technology layer.
    """

    @staticmethod
    def get_partner_payment_details(
        db: Session,
        partner_id: str,
    ) -> dict:
        """
        Get partner's payment collection account details.
        Payments must go to THEIR account, not ours.
        """
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise ValueError(f"Partner {partner_id} not found")

        api_config = db.query(PartnerApiConfig).filter(
            PartnerApiConfig.partner_id == partner_id
        ).first()

        return {
            "partner_id": partner.id,
            "partner_name": partner.name,
            "collection_account_id": partner.collection_account_id,
            "webhook_url": api_config.webhook_url if api_config else None,
        }

    @staticmethod
    def log_payment_routing(
        db: Session,
        artisan_phone: str,
        amount: int,
        partner_id: str,
        provider: str,
        transaction_ref: str,
        subscription_id: str = None,
    ) -> dict:
        """
        Log that a payment was routed to a partner insurer.

        CRITICAL: This logs ROUTING, not COLLECTION.
        Wali facilitated the connection; the money went to the partner.
        """
        from app.models.financial_event import FinancialEvent
        import uuid
        import hashlib

        # Get latest hash for chain integrity
        latest = (
            db.query(FinancialEvent)
            .order_by(FinancialEvent.created_at.desc())
            .first()
        )
        previous_hash = latest.compliance_hash if latest else "GENESIS"

        event = FinancialEvent(
            event_type="payment_routed",
            amount=amount,
            currency="XOF",
            partner_id=partner_id,
            provider=provider,
            provider_ref=transaction_ref,
            transaction_id=f"ROUTE-{uuid.uuid4().hex[:12]}",
            wali_role="technology_provider",
            routed_to_partner=True,  # Money went to partner, not Wali
        )

        if subscription_id:
            event.subscription_id = subscription_id

        # Compute compliance hash
        event.previous_hash = previous_hash
        event.compliance_hash = event.calculate_hash(previous_hash)

        db.add(event)
        db.commit()

        logger.info(
            "Payment ROUTED to %s: %d XOF via %s (ref: %s). Wali role: technology_provider",
            partner_id, amount, provider, transaction_ref,
        )

        return {
            "status": "routed_to_partner",
            "partner_id": partner_id,
            "amount": amount,
            "transaction_ref": transaction_ref,
            "wali_role": "technology_provider",
            "message": f"Paiement transmis directement à {partner_id} Assurances",
        }
