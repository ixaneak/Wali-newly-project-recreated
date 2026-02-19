"""
Suspicious Activity Report (SAR) Model

CIMA AML compliance — stores formal SARs generated from risk events.
Reports are filed with TRACFIN (Ivory Coast financial intelligence unit)
within 30 days of detection. Records retained for 5 years.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, CheckConstraint, Index
from sqlalchemy.types import JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum
from datetime import datetime, timedelta


class SarStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CLOSED = "closed"


class SubjectType(str, enum.Enum):
    POLICYHOLDER = "policyholder"
    BENEFICIARY = "beneficiary"
    THIRD_PARTY = "third_party"
    AGENT = "agent"


def _generate_reference():
    """Generate SAR reference: SAR-YYYY-NNNNNN."""
    year = datetime.utcnow().strftime("%Y")
    short_id = uuid.uuid4().hex[:6].upper()
    return f"SAR-{year}-{short_id}"


def _retention_date():
    """5-year retention from detection per CIMA regulations."""
    return datetime.utcnow() + timedelta(days=5 * 365)


class SarReport(Base):
    __tablename__ = "sar_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_reference = Column(String(50), unique=True, nullable=False, default=_generate_reference)
    status = Column(String(20), nullable=False, default=SarStatus.DRAFT.value)

    # Subject (who is suspicious)
    subject_type = Column(String(20), nullable=False)
    subject_id = Column(String(100), nullable=False)  # user ID or phone number
    subject_name = Column(String(255))
    subject_phone = Column(String(20))

    # Activity details
    activity_type = Column(String(50), nullable=False)  # rapid_claim, structuring, etc.
    detection_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    occurrence_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=False)

    # Financial details
    amount_involved = Column(Integer)  # XOF
    currency = Column(String(3), default="XOF")
    related_transactions = Column(JSON)  # Array of transaction IDs

    # Evidence
    supporting_documents = Column(JSON)  # File references
    risk_score = Column(Integer)  # 0-100

    # Compliance workflow
    assigned_analyst = Column(String(100))
    review_notes = Column(Text)
    tracfin_reference = Column(String(100))  # Reference from TRACFIN after submission

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True))
    retention_until = Column(DateTime(timezone=True), default=_retention_date)

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'submitted', 'under_review', 'closed')",
            name="sar_valid_status",
        ),
        CheckConstraint(
            "subject_type IN ('policyholder', 'beneficiary', 'third_party', 'agent')",
            name="sar_valid_subject_type",
        ),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="sar_valid_risk_score"),
        Index("idx_sar_status", "status"),
        Index("idx_sar_date", "detection_date"),
        Index("idx_sar_subject", "subject_id"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "report_reference": self.report_reference,
            "status": self.status,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "subject_name": self.subject_name,
            "subject_phone": self.subject_phone,
            "activity_type": self.activity_type,
            "detection_date": self.detection_date.isoformat() if self.detection_date else None,
            "occurrence_date": self.occurrence_date.isoformat() if self.occurrence_date else None,
            "description": self.description,
            "amount_involved": self.amount_involved,
            "currency": self.currency,
            "related_transactions": self.related_transactions,
            "risk_score": self.risk_score,
            "assigned_analyst": self.assigned_analyst,
            "review_notes": self.review_notes,
            "tracfin_reference": self.tracfin_reference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "retention_until": self.retention_until.isoformat() if self.retention_until else None,
        }
