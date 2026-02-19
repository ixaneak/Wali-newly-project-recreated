"""
Claims and Fraud Detection Models.

SQLAlchemy 2.0 async models for:
- Claims processing
- Fraud detection audit trail
- ARTCI/CIMA compliance
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ClaimType(str, enum.Enum):
    """Types of insurance claims."""
    PHARMACY = "pharmacy"
    HOSPITALIZATION = "hospitalization"
    ACCIDENT = "accident"
    DEATH = "death"


class ClaimStatus(str, enum.Enum):
    """Status of claim processing."""
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    FRAUD_REVIEW = "fraud_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SETTLED = "settled"
    SETTLEMENT_FAILED = "settlement_failed"


class FraudCheckType(str, enum.Enum):
    """Types of fraud checks performed."""
    PERCEPTUAL_HASH = "perceptual_hash"
    GPS_DISTANCE = "gps_distance"
    EXIF_TIMESTAMP = "exif_timestamp"
    SCREENSHOT = "screenshot"
    VELOCITY = "velocity"
    DEVICE_MISMATCH = "device_mismatch"


class FraudCheckResult(str, enum.Enum):
    """Result of fraud check."""
    PASS = "pass"
    FAIL = "fail"
    SUSPICIOUS = "suspicious"


class Claim(Base):
    """
    Insurance claim model.
    
    Stores all claim data including fraud detection results.
    Optimized for ARTCI/CIMA audit queries.
    """
    __tablename__ = "claims"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Artisan information
    artisan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artisans.id"),
        nullable=False,
        index=True
    )
    artisan_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="E.164 format (+22507XXXXXXXX)"
    )
    
    # Claim details
    claim_type: Mapped[ClaimType] = mapped_column(
        Enum(ClaimType, name="claimtype"),
        nullable=False
    )
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, name="claimstatus"),
        nullable=False,
        default=ClaimStatus.SUBMITTED,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Amount in XOF (West African CFA franc)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User description from WhatsApp"
    )
    
    # Image and forensics
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Backblaze B2 URL"
    )
    image_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Perceptual hash for deduplication"
    )
    
    # Pharmacy reference (if pharmacy claim)
    pharmacy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pharmacies.id"),
        nullable=True,
        index=True
    )
    
    # Fraud detection results
    fraud_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Risk score 0.0 to 1.0"
    )
    fraud_flags: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of fraud flags: DUPLICATE_IMAGE, GPS_MISMATCH, etc."
    )
    
    # EXIF metadata
    exif_gps: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment='{"lat": float, "lon": float}'
    )
    exif_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Original photo capture time"
    )
    device_fingerprint: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Hashed device ID from WhatsApp metadata"
    )
    
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    settled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Settlement tracking
    settlement_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="Mobile money transaction reference"
    )
    settled_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Actual amount settled (after 20% deductible)"
    )
    
    # Review
    reviewer_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes from manual review"
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    artisan = relationship("Artisan", back_populates="claims")
    pharmacy = relationship("Pharmacy", back_populates="claims")
    fraud_logs = relationship("FraudLog", back_populates="claim", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Claim(id={self.id}, status={self.status}, score={self.fraud_score:.2f})>"
    
    @property
    def short_id(self) -> str:
        """Short reference for WhatsApp notifications."""
        return str(self.id)[:8].upper()
    
    @property
    def is_suspicious(self) -> bool:
        """Check if claim needs manual review."""
        return self.fraud_score >= 0.7
    
    @property
    def settlement_amount(self) -> Decimal:
        """Calculate settlement amount (80% after 20% deductible)."""
        if self.amount:
            return Decimal(str(self.amount)) * Decimal("0.8")
        return Decimal("0")


class FraudLog(Base):
    """
    Fraud detection audit trail.
    
    ARTCI/CIMA compliance requirement:
    - All fraud checks must be logged
    - Raw data preserved for appeals
    """
    __tablename__ = "fraud_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id"),
        nullable=False,
        index=True
    )
    
    check_type: Mapped[FraudCheckType] = mapped_column(
        Enum(FraudCheckType, name="fraudchecktype"),
        nullable=False
    )
    result: Mapped[FraudCheckResult] = mapped_column(
        Enum(FraudCheckResult, name="fraudcheckresult"),
        nullable=False
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Confidence score for this check"
    )
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Raw data for appeals and audit"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    
    # Relationship
    claim = relationship("Claim", back_populates="fraud_logs")
    
    def __repr__(self) -> str:
        return f"<FraudLog(claim={self.claim_id}, type={self.check_type}, result={self.result})>"


class DataTransferLog(Base):
    """
    Cross-border data transfer log for ARTCI compliance.
    
    Law 2013-450 requires logging all transfers outside Côte d'Ivoire.
    """
    __tablename__ = "data_transfer_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id"),
        nullable=True,
        index=True
    )
    
    transfer_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="image_upload, fraud_analysis, etc."
    )
    destination: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="USA/Backblaze, Ireland/Meta, etc."
    )
    data_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="image, metadata, analysis_result"
    )
    legal_basis: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="contract_performance",
        comment="consent, contract_performance, legal_obligation"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<DataTransferLog(type={self.transfer_type}, dest={self.destination})>"


# Indexes for performance
Index("idx_claims_status_score", Claim.status, Claim.fraud_score)
Index("idx_claims_phone_submitted", Claim.artisan_phone, Claim.submitted_at)
Index("idx_fraud_logs_claim", FraudLog.claim_id, FraudLog.created_at)
Index("idx_data_transfer_claim", DataTransferLog.claim_id, DataTransferLog.created_at)
