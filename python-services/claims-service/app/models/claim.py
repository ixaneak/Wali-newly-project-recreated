"""
Incident Report Model (was: Claim)

IMPORTANT: Wali does NOT process insurance claims. We collect incident reports
from artisans and forward them to the partner insurer (NSIA) for processing.
The partner insurer makes all claim decisions and payouts.
"""
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class IncidentStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    FORWARDED_TO_PARTNER = "forwarded_to_partner"
    PARTNER_APPROVED = "partner_approved"
    PARTNER_REJECTED = "partner_rejected"
    PARTNER_PAID = "partner_paid"  # Partner handled payout, not us


class IncidentReport(Base):
    """
    Incident report filed by artisan, forwarded to partner insurer.

    Wali provides the technology layer for incident reporting.
    All claim decisions and payouts are handled by the partner insurer.
    """
    __tablename__ = "incident_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(128), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), nullable=False)
    incident_number = Column(String(50), unique=True, nullable=False)

    # Partner who handles this incident
    partner_id = Column(String(50), nullable=False, default="NSIA")

    # Incident details
    incident_type = Column(String(50), nullable=False)  # Product ID from partner, not our enum
    description = Column(Text, nullable=False)
    reported_amount = Column(Integer, nullable=False)
    partner_approved_amount = Column(Integer)  # Set by partner, not by us

    # Documentation
    image_urls = Column(ARRAY(Text))
    image_hashes = Column(ARRAY(Text))  # Perceptual hashes for fraud detection
    exif_data = Column(JSONB)

    # Status and review
    status = Column(Enum(IncidentStatus), default=IncidentStatus.SUBMITTED)
    reviewer_id = Column(String(128))
    review_notes = Column(Text)

    # Fraud detection (tech service we provide)
    fraud_score = Column(Integer, default=0)  # 0-100 risk score
    fraud_flags = Column(JSONB)  # Detailed fraud analysis

    # Partner processing (partner handles payout, not us)
    partner_reference = Column(String(100))  # Partner's claim/case number
    forwarded_to_partner_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True))

    def to_dict(self):
        """Convert incident report to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "subscription_id": str(self.subscription_id),
            "partner_id": self.partner_id,
            "incident_number": self.incident_number,
            "incident_type": self.incident_type,
            "description": self.description,
            "reported_amount": self.reported_amount,
            "partner_approved_amount": self.partner_approved_amount,
            "image_urls": self.image_urls,
            "exif_data": self.exif_data,
            "status": self.status.value,
            "reviewer_id": str(self.reviewer_id) if self.reviewer_id else None,
            "review_notes": self.review_notes,
            "fraud_score": self.fraud_score,
            "fraud_flags": self.fraud_flags,
            "partner_reference": self.partner_reference,
            "forwarded_to_partner_at": self.forwarded_to_partner_at.isoformat() if self.forwarded_to_partner_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


# Backward-compatible aliases for migration period
Claim = IncidentReport
ClaimStatus = IncidentStatus
