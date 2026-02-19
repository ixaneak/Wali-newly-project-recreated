from sqlalchemy import Column, String, Enum, DateTime
import enum
from app.core.database import Base

# Matching policy-service enums
class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class CoverageSubscription(Base):
    __tablename__ = "coverage_subscriptions"
    # We only need the columns we intend to read/update
    id = Column(String(36), primary_key=True)
    partner_id = Column(String(50)) # Added for mock integration lookup
    status = Column(Enum(SubscriptionStatus))
    mobile_money_ref = Column(String(100))
    last_payment_date = Column(DateTime(timezone=True))
    next_payment_date = Column(DateTime(timezone=True))
