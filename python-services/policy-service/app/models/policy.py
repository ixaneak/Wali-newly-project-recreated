from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, CheckConstraint, Text, JSON
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    ARTISAN = "artisan"
    PHARMACY = "pharmacy"
    ADMIN = "admin"
    USER = "user"

class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class PaymentFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class ProductType(str, enum.Enum):
    FUNERAL = "funeral"  # Deuil - most demanded
    HEALTH = "health"    # Simple hospitalization
    TRANSPORT = "transport"  # Moto/gbaka drivers
    AGRICULTURE = "agriculture"  # Cocoa/coffee farmers

class CoverageSubscription(Base):
    __tablename__ = "coverage_subscriptions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_number = Column(String(50), unique=True, nullable=False)
    partner_id = Column(String(50), ForeignKey("partners.id"), nullable=False, default="NSIA")
    partner_product_id = Column(String(100), nullable=False)
    partner_product_config = Column(JSON, nullable=False)
    partner_quoted_amount = Column(Integer, nullable=False)
    payment_frequency = Column(Enum(PaymentFrequency), nullable=False)
    coverage_type = Column(Enum(ProductType), default=ProductType.HEALTH)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    mobile_money_ref = Column(String(100))
    last_payment_date = Column(DateTime(timezone=True))
    next_payment_date = Column(DateTime(timezone=True))
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('partner_quoted_amount > 0', name='positive_quoted_amount'),
        CheckConstraint('end_date IS NULL OR end_date > start_date', name='valid_dates_check'),
    )

Policy = CoverageSubscription
PolicyStatus = SubscriptionStatus

class KYCStatus(str, enum.Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(String(128), primary_key=True)
    phone = Column(String(20), unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    name = Column(String(100))
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    avatar_url = Column(String(255))
    region = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
