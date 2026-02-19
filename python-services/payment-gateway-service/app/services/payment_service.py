from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.payment import PaymentTransaction, PaymentStatus
from app.models.policy import CoverageSubscription, SubscriptionStatus
from app.services.sms_service import SmsService

logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    def process_payment(
        db: Session, 
        provider: str, 
        transaction_id: str, 
        amount: int, 
        status: PaymentStatus,
        policy_id: str | None = None
    ):
        # 1. Idempotency Check
        existing_txn = db.query(PaymentTransaction).filter(
            PaymentTransaction.transaction_id == transaction_id,
            PaymentTransaction.provider == provider
        ).first()
        
        if existing_txn:
            logger.info(f"Duplicate transaction received: {transaction_id}")
            return existing_txn

        # 2. Record Transaction
        txn = PaymentTransaction(
            transaction_id=transaction_id,
            provider=provider,
            amount=amount,
            status=status,
            subscription_id=policy_id
        )
        db.add(txn)
        
        # 3. Update Policy if successful
        if status == PaymentStatus.SUCCESS and policy_id:
            policy = db.query(CoverageSubscription).filter(CoverageSubscription.id == policy_id).first()
            if policy:
                policy.status = SubscriptionStatus.ACTIVE
                policy.last_payment_date = datetime.now()
                # policy.next_payment_date = ... (calculate based on frequency)
                policy.mobile_money_ref = transaction_id
                db.add(policy)
                
                # 4. Send SMS
                # In a real app we'd get the user phone number via user_id -> User table
                SmsService.send_confirmation("UNKNOWN_NUMBER", f"Payment of {amount} FCFA received. Policy {policy_id} is now ACTIVE.")
                
            else:
                logger.error(f"Policy not found for payment: {policy_id}")

        db.commit()
        db.refresh(txn)
        return txn
