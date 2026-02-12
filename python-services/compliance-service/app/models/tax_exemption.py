"""
Tax Exemption Tracking — compliance-service copy.

SaaS model: tracks SaaS subscription revenue, platform service revenue,
and counts of payments routed and incidents forwarded.
"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class TaxExemptionTracking(Base):
    __tablename__ = "tax_exemption_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fiscal_year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)

    # SaaS Revenue Segregation
    tax_exempt_revenue = Column(Integer, default=0)      # Payments routed to partner (not Wali revenue)
    taxable_revenue = Column(Integer, default=0)          # SaaS subscription + platform fees

    # SaaS Metrics
    saas_subscription_revenue = Column(Integer, default=0)
    platform_service_revenue = Column(Integer, default=0)
    total_payments_routed = Column(Integer, default=0)     # Count of payments forwarded to partners
    total_incidents_forwarded = Column(Integer, default=0) # Count of incidents forwarded

    # Report
    xml_report_path = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "fiscal_year": self.fiscal_year,
            "quarter": self.quarter,
            "tax_exempt_revenue": self.tax_exempt_revenue,
            "taxable_revenue": self.taxable_revenue,
            "saas_subscription_revenue": self.saas_subscription_revenue,
            "platform_service_revenue": self.platform_service_revenue,
            "total_payments_routed": self.total_payments_routed,
            "total_incidents_forwarded": self.total_incidents_forwarded,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
