"""
Tax Exemption Tracking

Tracks Wali's Label Startup 3-year tax exemption status.
Revenue is from SaaS subscriptions (software license fees),
NOT from insurance premiums or commissions.
"""
from sqlalchemy import Column, String, Integer, DateTime, Numeric
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class TaxExemptionTracking(Base):
    __tablename__ = "tax_exemption_tracking"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fiscal_year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)

    # Revenue Segregation — SaaS Model
    saas_subscription_revenue = Column(Integer, default=0)    # Monthly license fees from partners
    platform_service_revenue = Column(Integer, default=0)     # Additional platform service charges
    total_payments_routed = Column(Integer, default=0)        # Payments routed TO partners (not our revenue)
    total_incidents_forwarded = Column(Integer, default=0)    # Incidents forwarded TO partners (not claims we paid)

    # Compliance Status
    cosumaf_report_status = Column(String(20), default='generated')  # generated, submitted, approved
    xml_report_path = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "fiscal_year": self.fiscal_year,
            "quarter": self.quarter,
            "saas_subscription_revenue": self.saas_subscription_revenue,
            "platform_service_revenue": self.platform_service_revenue,
            "total_payments_routed": self.total_payments_routed,
            "total_incidents_forwarded": self.total_incidents_forwarded,
            "cosumaf_status": self.cosumaf_report_status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
