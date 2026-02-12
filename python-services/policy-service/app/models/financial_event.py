from sqlalchemy import Column, String, Integer, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import hashlib

class FinancialEvent(Base):
    __tablename__ = "financial_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False)  # payment_routed, claim_forwarded, saas_fee_received, tech_fee
    amount = Column(Integer, nullable=False)  # XOF only, never floats
    currency = Column(String(3), default='XOF', nullable=False)
    user_id = Column(String(36), nullable=True)
    subscription_id = Column(String(36), nullable=True)  # was: policy_id
    partner_id = Column(String(50), nullable=True)  # Which partner insurer received the money
    provider = Column(String(50), nullable=True)  # orange_money, mtn_momo, wave, paydunya
    provider_ref = Column(String(200), nullable=True)
    transaction_id = Column(String(200), unique=True, nullable=False)

    # Wali role declaration
    wali_role = Column(String(50), default='technology_provider')  # Always technology_provider

    # Compliance Chain
    compliance_hash = Column(String(64), unique=True, nullable=False)  # SHA-256 chain
    previous_hash = Column(String(64), nullable=False)  # cryptographic chaining
    routed_to_partner = Column(Boolean, default=True)  # TRUE = payment went to insurer, not Wali

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_compliance_created', 'created_at', 'event_type'),
    )

    def calculate_hash(self, previous_hash_val: str) -> str:
        data_string = f"{previous_hash_val}{self.transaction_id}{self.amount}{self.event_type}{self.user_id}"
        return hashlib.sha256(data_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "amount": self.amount,
            "currency": self.currency,
            "partner_id": self.partner_id,
            "wali_role": self.wali_role,
            "transaction_id": self.transaction_id,
            "compliance_hash": self.compliance_hash,
            "previous_hash": self.previous_hash,
            "routed_to_partner": self.routed_to_partner,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
