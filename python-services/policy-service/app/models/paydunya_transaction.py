"""
PayDunya Transaction Model — Payment Routing Tracker

Tracks all PayDunya payment routing transactions.
Payments are routed to partner insurers, NOT collected by Wali.
"""
import enum
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class PaydunyaStatus(str, enum.Enum):
    """Payment routing status."""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PaydunyaTransaction(Base):
    """Track all PayDunya payment routing transactions."""
    __tablename__ = "paydunya_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    internal_ref = Column(String(100), unique=True, nullable=False)

    # PayDunya specifics
    paydunya_token = Column(String(255), unique=True)
    paydunya_ref = Column(String(255), nullable=True)
    checkout_url = Column(String(500))

    # Financial
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), default="XOF")
    amount_customer_paid = Column(Integer)
    paydunya_fees = Column(Integer)

    # Status
    status = Column(Enum(PaydunyaStatus), default=PaydunyaStatus.PENDING)
    provider = Column(String(50))  # orange_money, mtn_momo, wave, moov
    failure_reason = Column(Text, nullable=True)

    # SaaS references (was: policy_id → coverage_subscriptions)
    subscription_id = Column(String(36), ForeignKey("coverage_subscriptions.id"), nullable=True)
    user_id = Column(String(128), ForeignKey("users.id"), nullable=True)
    partner_id = Column(String(50), nullable=True)

    # Metadata
    metadata_json = Column(JSON)
    raw_webhook_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    def to_dict(self):
        return {
            "id": str(self.id),
            "internal_ref": self.internal_ref,
            "paydunya_token": self.paydunya_token,
            "checkout_url": self.checkout_url,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value if isinstance(self.status, PaydunyaStatus) else self.status,
            "provider": self.provider,
            "subscription_id": str(self.subscription_id) if self.subscription_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "partner_id": self.partner_id,
            "wali_role": "technology_provider",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
