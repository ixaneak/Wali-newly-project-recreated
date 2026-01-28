from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, CheckConstraint, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    ARTISAN = "artisan"
    PHARMACY = "pharmacy"
    ADMIN = "admin"


class PolicyStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class CoverageType(str, enum.Enum):
    HEALTH = "health"
    EQUIPMENT = "equipment"
    THEFT = "theft"
    BUNDLE = "bundle"


class PaymentFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Policy(Base):
    """Insurance policy model."""
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    policy_number = Column(String(50), unique=True, nullable=False)
    
    # Coverage details
    coverage_type = Column(Enum(CoverageType), nullable=False)
    coverage_details = Column(JSONB, nullable=False)
    premium_amount = Column(Integer, nullable=False)
    payment_frequency = Column(Enum(PaymentFrequency), nullable=False)
    status = Column(Enum(PolicyStatus), default=PolicyStatus.PENDING)
    
    # Payment tracking
    mobile_money_ref = Column(String(100))
    last_payment_date = Column(DateTime(timezone=True))
    next_payment_date = Column(DateTime(timezone=True))
    
    # Policy lifecycle
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('premium_amount > 0', name='positive_premium'),
        CheckConstraint('end_date IS NULL OR end_date > start_date', name='valid_dates'),
    )
    
    def to_dict(self):
        """Convert policy to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "policy_number": self.policy_number,
            "coverage_type": self.coverage_type.value,
            "coverage_details": self.coverage_details,
            "premium_amount": self.premium_amount,
            "payment_frequency": self.payment_frequency.value,
            "status": self.status.value,
            "mobile_money_ref": self.mobile_money_ref,
            "last_payment_date": self.last_payment_date.isoformat() if self.last_payment_date else None,
            "next_payment_date": self.next_payment_date.isoformat() if self.next_payment_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class User(Base):
    """User model (simplified for policy service)."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    region = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
