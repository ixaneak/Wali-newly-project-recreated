from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import hashlib

class FinancialEvent(Base):
    __tablename__ = "financial_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)  # premium_collected, claim_paid, commission, tax
    amount = Column(Integer, nullable=False)  # XOF only, never floats
    currency = Column(String(3), default='XOF', nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    policy_id = Column(UUID(as_uuid=True), nullable=True)
    provider = Column(String(50), nullable=True)  # orange_money, mtn_momo, wave
    provider_ref = Column(String(200), nullable=True)
    transaction_id = Column(String(200), unique=True, nullable=False)
    
    # Compliance Chain
    compliance_hash = Column(String(64), unique=True, nullable=False)  # SHA-256 chain
    previous_hash = Column(String(64), nullable=False)  # cryptographic chaining
    escrow_segregated = Column(Boolean, default=False)  # TRUE = tax exempt premium
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_compliance_created', 'created_at', 'event_type'),
    )

    def calculate_hash(self, previous_hash_val: str) -> str:
        """
        Generates SHA-256 hash based on previous hash and current data
        Constraint: Tamper-evident chaining
        """
        data_string = f"{previous_hash_val}{self.transaction_id}{self.amount}{self.event_type}{self.user_id}"
        return hashlib.sha256(data_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "amount": self.amount,
            "currency": self.currency,
            "transaction_id": self.transaction_id,
            "compliance_hash": self.compliance_hash,
            "previous_hash": self.previous_hash,
            "escrow_segregated": self.escrow_segregated,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
