from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payment_service import PaymentService
from app.models.payment import PaymentStatus
from app.schemas.payment import OrangeMoneyWebhook, WaveWebhook, MtnMomoWebhook

router = APIRouter()

@router.post("/orange-money", status_code=200)
async def handle_orange_money_webhook(
    payload: OrangeMoneyWebhook, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Map status
    status = PaymentStatus.SUCCESS if payload.status == "SUCCESS" else PaymentStatus.FAILED
    
    # Process in background if needed, or inline for simplicity first
    # For now inline to ensure DB consistency
    PaymentService.process_payment(
        db, 
        provider="orange_money",
        transaction_id=payload.txnid,
        amount=payload.amount,
        status=status,
        policy_id=payload.ref_id # Assuming ref_id corresponds to our subscription_id
    )
    return {"status": "received"}

@router.post("/wave", status_code=200)
async def handle_wave_webhook(
    payload: WaveWebhook, 
    db: Session = Depends(get_db)
):
    status = PaymentStatus.SUCCESS if payload.checkout_status == "complete" else PaymentStatus.FAILED
    
    PaymentService.process_payment(
        db,
        provider="wave",
        transaction_id=payload.id,
        amount=int(payload.amount),
        status=status,
        policy_id=payload.client_reference
    )
    return {"status": "received"}

@router.post("/mtn-momo", status_code=200)
async def handle_mtn_momo_webhook(
    payload: MtnMomoWebhook,
    db: Session = Depends(get_db)
):
    status = PaymentStatus.SUCCESS if payload.status == "SUCCESSFUL" else PaymentStatus.FAILED
    
    PaymentService.process_payment(
        db,
        provider="mtn_momo",
        transaction_id=payload.externalId, # externalId usually maps to our ref
        amount=int(payload.amount),
        status=status,
        policy_id=payload.externalId # Assuming we sent policy_id as externalId
    )
    return {"status": "received"}
