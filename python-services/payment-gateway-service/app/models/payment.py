from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.sql import func
import enum
import uuid
from app.core.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(100), unique=True, nullable=False) # External ID from provider
    provider = Column(String(50), nullable=False) # orange_money, wave, mtn_momo
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), default="XOF")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Link to Policy Service Tables (Foreign Keys might not be enforceable if cross-service, 
    # but since it's a shared DB for now, we can link them or just store the ID)
    subscription_id = Column(String(36), nullable=True) # ID of the policy/subscription
    
    raw_response = Column(Text, nullable=True) # Store full webhook payload for debugging
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
