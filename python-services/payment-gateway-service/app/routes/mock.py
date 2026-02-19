from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
import requests
import logging
from app.core.database import get_db
from app.core.config import get_settings
from app.services.payment_service import PaymentService
from app.models.payment import PaymentStatus
from app.models.policy import CoverageSubscription, SubscriptionStatus

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

@router.post("/mock-payment")
def mock_payment(
    policy_id: str, 
    phone: str = "+22501234567", 
    amount: int = 1000,
    db: Session = Depends(get_db)
):
    """
    Simulate successful Orange Money payment and trigger policy activation.
    """
    # 1. Generate fake transaction_id
    transaction_id = f"MOCK-OM-{uuid.uuid4()}"
    
    # 2. Create payment record in DB (status: success)
    # We use PaymentService to keep logic consistent
    payment = PaymentService.process_payment(
        db,
        provider="orange_money_mock",
        transaction_id=transaction_id,
        amount=amount,
        status=PaymentStatus.SUCCESS,
        policy_id=policy_id
    )
    
    # 3. Call policy-service to activate policy (HTTP POST)
    # First, find partner_id
    policy = db.query(CoverageSubscription).filter(CoverageSubscription.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    partner_id = policy.partner_id
    if not partner_id:
        # Fallback or error? Let's assume NSIA if missing for now or error
        logger.warning(f"Policy {policy_id} has no partner_id, defaulting to NSIA for mock")
        partner_id = "NSIA"

    # Call Policy Service
    try:
        url = f"{settings.policy_service_url}/api/v1/partners/{partner_id}/enrollments/{policy_id}/confirm"
        payload = {"transaction_ref": transaction_id}
        logger.info(f"Calling Policy Service: {url} with {payload}")
        
        # We assume policy service is running. If not, this might fail.
        # Capturing expected failure handling for dev environment
        try:
            resp = requests.post(url, json=payload, timeout=5)
            resp.raise_for_status()
            logger.info(f"Policy Service response: {resp.json()}")
        except requests.exceptions.ConnectionError:
            logger.warning("Policy Service not reachable. Mock payment recorded locally only.")
            # We don't fail the request completely if just testing payment service isolation
    
    except Exception as e:
        logger.error(f"Failed to call policy service: {e}")
        
    return {
        "status": "success",
        "transaction_id": transaction_id,
        "message": "Mock payment processed and policy activation triggered"
    }

@router.post("/mock-webhook")
def mock_webhook(
    policy_id: str, 
    status: str = "SUCCESS",
    amount: int = 5000,
    provider: str = "orange_money",
    db: Session = Depends(get_db)
):
    """
    Simulate provider webhook callback.
    """
    payment_status = PaymentStatus.SUCCESS if status == "SUCCESS" else PaymentStatus.FAILED
    transaction_id = f"MOCK-WEBHOOK-{uuid.uuid4()}"
    
    PaymentService.process_payment(
        db,
        provider=provider,
        transaction_id=transaction_id,
        amount=amount,
        status=payment_status,
        policy_id=policy_id
    )
    
    return {"status": "received", "transaction_id": transaction_id}
