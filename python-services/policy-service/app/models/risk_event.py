"""
Risk Event Model

Raw detection log — every time a risk rule fires, an event is created here.
Events with high severity can be escalated to formal SAR reports.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.types import JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False)  # structuring, rapid_claim, etc.
    severity = Column(String(20), nullable=False, default=RiskSeverity.LOW.value)

    # Context references
    policy_id = Column(String(100))
    claim_id = Column(String(100))
    user_phone = Column(String(20))
    user_id = Column(String(128))

    # Scoring
    risk_score = Column(Integer)  # 0-100
    triggered_rules = Column(JSON)  # Which rules fired, e.g. ["rapid_claim", "round_number"]
    raw_data = Column(JSON)  # Full context for investigation

    # Escalation
    sar_report_id = Column(String(36), ForeignKey("sar_reports.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="risk_valid_severity",
        ),
        Index("idx_risk_severity", "severity"),
        Index("idx_risk_created", "created_at"),
        Index("idx_risk_user", "user_id"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "severity": self.severity,
            "policy_id": self.policy_id,
            "claim_id": self.claim_id,
            "user_phone": self.user_phone,
            "user_id": self.user_id,
            "risk_score": self.risk_score,
            "triggered_rules": self.triggered_rules,
            "raw_data": self.raw_data,
            "sar_report_id": self.sar_report_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
