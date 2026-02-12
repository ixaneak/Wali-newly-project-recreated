"""
PayDunya Payment Routing Routes

Routes artisan payments to partner insurer via PayDunya.
Wali provides the technology; money goes to the partner's account.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security_middleware import verify_jwt
from app.services.paydunya_service import (
    create_paydunya_invoice,
    process_paydunya_webhook,
    get_transaction_status,
)

router = APIRouter(prefix="/api/v1/partners", tags=["payment-routing"])
logger = logging.getLogger(__name__)


# ── Schemas ─────────────────────────────────────────────────────

class PaymentRouteRequest(BaseModel):
    """Request to route payment to partner via PayDunya."""
    subscription_id: str = Field(..., description="Coverage subscription ID")
    user_phone: str = Field(..., description="Artisan's phone number")
    user_name: Optional[str] = "Artisan"


class PaymentRouteResponse(BaseModel):
    status: str
    internal_ref: str
    amount: int
    partner_id: str
    wali_role: str = "technology_provider"
    checkout_url: Optional[str] = None
    message: Optional[str] = None


# ── Routes ──────────────────────────────────────────────────────

@router.post(
    "/{partner_id}/payments/route",
    response_model=PaymentRouteResponse,
    status_code=status.HTTP_201_CREATED,
)
def initiate_payment_routing(
    partner_id: str,
    request: PaymentRouteRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """
    Route artisan payment to partner insurer via PayDunya.

    IMPORTANT: Money goes DIRECTLY to the partner's PayDunya account.
    Wali provides the technology layer only.
    """
    try:
        result = create_paydunya_invoice(
            db=db,
            subscription_id=request.subscription_id,
            user_phone=request.user_phone,
            user_name=request.user_name or "Artisan",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("PayDunya routing error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment routing service unavailable",
        )


@router.post("/{partner_id}/payments/webhook")
async def paydunya_webhook(
    partner_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    PayDunya IPN callback (no auth — hash-verified).

    Processes payment confirmation and logs as ROUTED to partner,
    not as COLLECTED by Wali.
    """
    body = await request.json()
    paydunya_hash = request.headers.get("X-Paydunya-Signature", "")

    result = process_paydunya_webhook(
        db=db,
        payload=body,
        paydunya_hash=paydunya_hash,
    )

    if result.get("status") == "rejected":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    return result


@router.get("/{partner_id}/payments/verify/{internal_ref}")
def verify_payment_routing(
    partner_id: str,
    internal_ref: str,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    """Check status of a payment routing transaction."""
    result = get_transaction_status(db, internal_ref)
    if result["status"] == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return result


@router.get("/{partner_id}/payments/test-numbers")
def get_test_numbers(partner_id: str):
    """Sandbox test phone numbers for each provider."""
    from app.config.paydunya import paydunya_config
    
    if paydunya_config.MODE != "test":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only available in test mode")

    return {
        "partner_id": partner_id,
        "wali_role": "technology_provider",
        "test_numbers": {
            "orange_money": "0700000000",
            "mtn_momo": "0500000000",
            "moov_money": "0100000000",
        },
    }
