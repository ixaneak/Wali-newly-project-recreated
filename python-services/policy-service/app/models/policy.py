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

    # QR Code System
    qr_token = Column(String, unique=True, index=True)
    qr_expires_at = Column(DateTime(timezone=True))
    verification_hash = Column(String)

    __table_args__ = (
        CheckConstraint('partner_quoted_amount > 0', name='positive_quoted_amount'),
        CheckConstraint('end_date IS NULL OR end_date > start_date', name='valid_dates_check'),
    )

    def generate_qr_token(self):
        """Generate a secure, unique QR token (2-min JWT for Pharmacy)."""
        import jwt
        import uuid
        import hashlib
        from datetime import datetime, timedelta
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # 2-minute token for max security against replay attacks
        self.qr_expires_at = datetime.utcnow() + timedelta(minutes=2)
        jti = str(uuid.uuid4())
        
        payload = {
            "sub": str(self.id),
            "jti": jti,
            "exp": self.qr_expires_at,
            "type": "pharmacy_qr"
        }
        
        self.qr_token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        
        # Store verification hash to prevent replay of the same token
        self.verification_hash = hashlib.sha256(self.qr_token.encode()).hexdigest()
        
        return self.qr_token

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
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

