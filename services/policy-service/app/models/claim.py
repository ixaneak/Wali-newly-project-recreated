from sqlalchemy import Column, String, DateTime, Numeric, Text, ForeignKey, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=True)
    
    # Claim details
    claim_type = Column(String(50), nullable=False)  # medical, accident, property, other
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=False)
    incident_date = Column(Date, nullable=False)
    
    # Status and review
    status = Column(String(50), nullable=False, default='submitted')  # submitted, under_review, approved, rejected, paid
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Photos
    photos = Column(JSON, nullable=True)  # Array of photo URLs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "policy_id": str(self.policy_id) if self.policy_id else None,
            "claim_type": self.claim_type,
            "amount": float(self.amount),
            "description": self.description,
            "incident_date": self.incident_date.isoformat() if self.incident_date else None,
            "status": self.status,
            "review_notes": self.review_notes,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "photos": self.photos,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
