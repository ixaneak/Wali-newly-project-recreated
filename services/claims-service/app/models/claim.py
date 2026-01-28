from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class ClaimStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class CoverageType(str, enum.Enum):
    HEALTH = "health"
    EQUIPMENT = "equipment"
    THEFT = "theft"
    BUNDLE = "bundle"


class Claim(Base):
    """Insurance claim model."""
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    claim_number = Column(String(50), unique=True, nullable=False)
    
    # Claim details
    claim_type = Column(Enum(CoverageType), nullable=False)
    description = Column(Text, nullable=False)
    claimed_amount = Column(Integer, nullable=False)
    approved_amount = Column(Integer)
    
    # Documentation
    image_urls = Column(ARRAY(Text))
    image_hashes = Column(ARRAY(Text))  # Perceptual hashes for fraud detection
    exif_data = Column(JSONB)
    
    # Status and review
    status = Column(Enum(ClaimStatus), default=ClaimStatus.SUBMITTED)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    review_notes = Column(Text)
    
    # Fraud detection
    fraud_score = Column(Integer, default=0)  # 0-100 risk score
    fraud_flags = Column(JSONB)  # Detailed fraud analysis
    
    # Payout
    payout_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    payout_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    
    def to_dict(self):
        """Convert claim to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "policy_id": str(self.policy_id),
            "claim_number": self.claim_number,
            "claim_type": self.claim_type.value,
            "description": self.description,
            "claimed_amount": self.claimed_amount,
            "approved_amount": self.approved_amount,
            "image_urls": self.image_urls,
            "exif_data": self.exif_data,
            "status": self.status.value,
            "reviewer_id": str(self.reviewer_id) if self.reviewer_id else None,
            "review_notes": self.review_notes,
            "fraud_score": self.fraud_score,
            "fraud_flags": self.fraud_flags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
