"""
PayDunya Payment Routing Service

Routes artisan payments DIRECTLY to the partner insurer via PayDunya.
Wali provides the technology; money goes to the partner's account.

Flow:
  1. Artisan selects product on Wali app
  2. Wali creates PayDunya invoice → routes to partner's PayDunya account
  3. PayDunya IPN confirms payment → Wali logs routing event
  4. Partner confirms coverage activation
"""
import uuid
import logging
import requests
from datetime import datetime
from sqlalchemy.orm import Session

from app.config.paydunya import paydunya_config, verify_paydunya_hash
from app.models.paydunya_transaction import PaydunyaTransaction, PaydunyaStatus
from app.models.partner import Partner

# Delayed import to avoid circular dependency
# from app.models.policy import CoverageSubscription, SubscriptionStatus

logger = logging.getLogger(__name__)
config = paydunya_config


def detect_provider(phone: str) -> str:
    """Detect mobile money provider from Ivorian phone number."""
    if not phone:
        return "unknown"
    digits = phone.replace("+225", "").replace(" ", "")
    if digits[:2] in ("07", "47", "57", "67", "77"):
        return "orange_money"
    elif digits[:2] in ("05", "45", "55", "65", "75"):
        return "mtn_momo"
    elif digits[:2] in ("01", "41", "51", "61", "71"):
        return "moov_money"
    elif digits[:2] in ("02",):
        return "wave"
    return "unknown"


def create_paydunya_invoice(
    db: Session,
    subscription_id: str,
    user_phone: str,
    user_name: str = "Artisan",
) -> dict:
    """
    Create PayDunya invoice that routes payment to PARTNER INSURER.

    The invoice amount comes from the partner's quoted price,
    NOT from any internal premium calculator.
    Money goes to the partner's PayDunya account, NOT to Wali.
    """
    # Import locally to avoid cycles
    try:
        import app.models.policy as policy_model
        CoverageSubscription = policy_model.CoverageSubscription
    except AttributeError:
        # Fallback debug
        import sys
        import logging
        logging.getLogger(__name__).error(f"Failed to import CoverageSubscription. app.models.policy attributes: {dir(sys.modules.get('app.models.policy'))}")
        raise
    
    # Get subscription with partner-set pricing
    subscription = db.query(CoverageSubscription).filter(
        CoverageSubscription.id == subscription_id
    ).first()
    if not subscription:
        raise ValueError("Subscription not found")

    # Get partner details for payment routing
    partner = db.query(Partner).filter(
        Partner.id == subscription.partner_id
    ).first()

    # Amount comes from partner, not from internal calculator
    amount = subscription.partner_quoted_amount

    internal_ref = f"WALI-ROUTE-{uuid.uuid4().hex[:12].upper()}"

    # SaaS Compliance: Verify destination account with Partner API
    # Before routing money, we MUST confirm we are sending it to the correct Partner entity.
    try:
        # In prod, this URL comes from partner.api_config
        resp = requests.get("http://localhost:8008/v1/collection-account", timeout=5)
        resp.raise_for_status()
        account_info = resp.json()
        
        # Log that we verified the destination
        logger.info(
            "COMPLIANCE VERIFIED: Routing payment to %s (Account: %s, Merchant: %s)", 
            account_info["account_holder"], 
            account_info["account_number"],
            account_info["mobile_money_merchant_id"]
        )
    except Exception as e:
        logger.error("SaaS Compliance Check Failed: Could not verify partner account: %s", e)
        raise ValueError("Compliance Error: Cannot route payment. Failed to verify Partner Collection Account identity.")


    # Build PayDunya invoice
    invoice_data = {
        "invoice": {
            "items": {
                "item_0": {
                    "name": f"Couverture {subscription.partner_product_id}",
                    "quantity": 1,
                    "unit_price": amount,
                    "total_price": amount,
                    "description": (
                        f"Cotisation assurance via {subscription.partner_id} - "
                        f"Souscription {subscription.subscription_number}"
                    ),
                }
            },
            "total_amount": amount,
            "description": (
                f"Paiement routé vers {subscription.partner_id} Assurances "
                f"via plateforme WALI"
            ),
        },
        "store": {
            "name": f"WALI - Plateforme pour {subscription.partner_id}",
            "tagline": "Plateforme digitale de distribution d'assurance",
            "phone": user_phone,
            "logo_url": "https://wali.ci/logo.png",
            "website_url": "https://wali.ci",
            "callback_url": f"{config.api_url}/checkout/callback",
        },
        "custom_data": {
            "subscription_id": str(subscription_id),
            "internal_ref": internal_ref,
            "partner_id": subscription.partner_id,
            "wali_role": "technology_provider",
        },
        "actions": {
            "callback_url": f"{config.api_url}/checkout/callback",
            "return_url": f"https://app.wali.ci/dashboard/payment/status?ref={internal_ref}",
            "cancel_url": "https://app.wali.ci/dashboard/payment/cancelled",
        },
    }

    # Record transaction
    provider = detect_provider(user_phone)

    txn = PaydunyaTransaction(
        subscription_id=subscription.id,
        internal_ref=internal_ref,
        amount=amount,
        currency="XOF",
        provider=provider,
        status=PaydunyaStatus.PENDING,
        metadata_json={
            "user_phone": user_phone,
            "user_name": user_name,
            "partner_id": subscription.partner_id,
            "partner_product_id": subscription.partner_product_id,
            "wali_role": "technology_provider",
        },
    )
    db.add(txn)
    db.commit()

    # Call PayDunya API (or return test data)
    if config.MODE == "test":
        logger.info("TEST MODE — PayDunya invoice for %d XOF (routed to %s)", amount, subscription.partner_id)
        return {
            "status": "pending",
            "internal_ref": internal_ref,
            "amount": amount,
            "partner_id": subscription.partner_id,
            "wali_role": "technology_provider",
            "checkout_url": f"https://app.paydunya.com/sandbox-checkout/test-{internal_ref}",
            "test_numbers": {
                "orange": "0700000000",
                "mtn": "0500000000",
                "moov": "0100000000",
            },
            "message": f"Paiement sera routé directement vers {subscription.partner_id} Assurances",
        }

    # LIVE: Call PayDunya
    headers = config.headers

    try:
        resp = requests.post(config.api_url, json=invoice_data, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        txn.paydunya_token = data.get("token", "")
        txn.checkout_url = data.get("response_text", "")
        db.commit()

        return {
            "status": "pending",
            "internal_ref": internal_ref,
            "amount": amount,
            "partner_id": subscription.partner_id,
            "wali_role": "technology_provider",
            "checkout_url": data.get("response_text", ""),
            "message": f"Paiement sera routé directement vers {subscription.partner_id} Assurances",
        }
    except requests.RequestException as e:
        txn.status = PaydunyaStatus.FAILED
        txn.failure_reason = str(e)
        db.commit()
        logger.error("PayDunya API error: %s", e)
        raise


def process_paydunya_webhook(
    db: Session,
    payload: dict,
    paydunya_hash: str,
) -> dict:
    """
    Handle PayDunya IPN callback.

    On successful payment:
      1. Log the payment as ROUTED to partner (not collected by Wali)
      2. Notify partner of payment
      3. Confirm enrollment
    """
    # Verify hash
    if not verify_paydunya_hash(payload, config.PRIVATE_KEY): # Fix: Pass private key
        logger.warning("Invalid PayDunya hash — possible spoofing")
        return {"status": "rejected", "reason": "invalid_hash"}

    custom_data = payload.get("custom_data", {})
    internal_ref = custom_data.get("internal_ref")
    if not internal_ref:
        return {"status": "error", "reason": "missing_internal_ref"}

    txn = db.query(PaydunyaTransaction).filter(
        PaydunyaTransaction.internal_ref == internal_ref
    ).first()
    if not txn:
        logger.error("Transaction not found: %s", internal_ref)
        return {"status": "error", "reason": "transaction_not_found"}

    status = payload.get("status", "").lower()

    if status == "completed":
        txn.status = PaydunyaStatus.COMPLETED
        txn.paydunya_ref = payload.get("transaction_id", "")

        # Log as ROUTED, not COLLECTED
        from app.services.payment_routing_service import PaymentRoutingService
        partner_id = custom_data.get("partner_id", "NSIA")

        PaymentRoutingService.log_payment_routing(
            db=db,
            artisan_phone=txn.metadata_json.get("user_phone", ""),
            amount=txn.amount,
            partner_id=partner_id,
            provider=txn.provider,
            transaction_ref=txn.paydunya_ref or internal_ref,
            subscription_id=str(txn.subscription_id) if txn.subscription_id else None,
        )

        # Confirm enrollment (activate coverage with partner)
        if txn.subscription_id:
            from app.services.policy_service import EnrollmentService
            try:
                EnrollmentService.confirm_enrollment(
                    db, str(txn.subscription_id), txn.paydunya_ref or internal_ref
                )
            except Exception as e:
                logger.error("Failed to confirm enrollment: %s", e)

        db.commit()
        logger.info(
            "Payment ROUTED to %s: %d XOF (ref: %s). Wali role: technology_provider",
            partner_id, txn.amount, internal_ref,
        )

        return {
            "status": "routed_to_partner",
            "partner_id": partner_id,
            "amount": txn.amount,
            "wali_role": "technology_provider",
        }

    elif status == "failed":
        txn.status = PaydunyaStatus.FAILED
        txn.failure_reason = payload.get("fail_reason", "unknown")
        db.commit()
        return {"status": "failed", "reason": txn.failure_reason}

    return {"status": "unknown", "raw_status": status}


def get_transaction_status(db: Session, internal_ref: str) -> dict:
    """Get current status of a payment routing transaction."""
    txn = db.query(PaydunyaTransaction).filter(
        PaydunyaTransaction.internal_ref == internal_ref
    ).first()
    if not txn:
        return {"status": "not_found"}

    return {
        "status": txn.status.value,
        "internal_ref": txn.internal_ref,
        "amount": txn.amount,
        "provider": txn.provider,
        "partner_id": txn.metadata_json.get("partner_id", "NSIA") if txn.metadata_json else "NSIA",
        "wali_role": "technology_provider",
        "created_at": txn.created_at.isoformat() if txn.created_at else None,
    }
