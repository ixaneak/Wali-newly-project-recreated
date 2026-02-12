import uuid
import enum
import secrets
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, Enum, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL_ENDED = "trial_ended"

class PharmacyPartner(Base):
    __tablename__ = "pharmacy_partners"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    
    business_name = Column(String(200), nullable=False)
    phone_contact = Column(String(50))
    location_city = Column(String(100))
    
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    trial_ends_at = Column(DateTime(timezone=True), default=lambda: datetime.now() + timedelta(days=14))
    subscription_renews_at = Column(DateTime(timezone=True))
    
    api_key = Column(String(256), unique=True, index=True)
    api_quota_daily = Column(Integer, default=1000)
    monthly_fee = Column(Integer, default=50000)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def check_subscription(self):
        now = datetime.now()
        if self.subscription_status == SubscriptionStatus.TRIAL:
            if self.trial_ends_at and now > self.trial_ends_at:
                self.subscription_status = SubscriptionStatus.TRIAL_ENDED
                return False
            return True
        return self.subscription_status == SubscriptionStatus.ACTIVE

    def to_dict(self):
        return {
            "id": str(self.id),
            "business_name": self.business_name,
            "email": self.email,
            "subscription_status": self.subscription_status.value,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "api_key": self.api_key
        }
