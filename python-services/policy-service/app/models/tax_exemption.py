from sqlalchemy import Column, String, Integer, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class TaxExemptionTracking(Base):
    __tablename__ = "tax_exemption_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fiscal_year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    
    # Revenue Segregation
    tax_exempt_revenue = Column(Integer, default=0)  # Insurance premiums (escrow)
    taxable_revenue = Column(Integer, default=0)     # Tech fees, commissions
    
    # Insurance Metrics
    total_premiums_collected = Column(Integer, default=0)
    total_claims_paid = Column(Integer, default=0)
    loss_ratio = Column(Numeric(5, 2), default=0.0)
    
    # Compliance Status
    cosumaf_report_status = Column(String(20), default='generated') # generated, submitted, approved
    xml_report_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def update_loss_ratio(self):
        if self.total_premiums_collected > 0:
            self.loss_ratio = (float(self.total_claims_paid) / float(self.total_premiums_collected)) * 100
        else:
            self.loss_ratio = 0.0

    def to_dict(self):
        return {
            "id": str(self.id),
            "fiscal_year": self.fiscal_year,
            "quarter": self.quarter,
            "tax_exempt_revenue": self.tax_exempt_revenue,
            "taxable_revenue": self.taxable_revenue,
            "loss_ratio": float(self.loss_ratio),
            "cosumaf_status": self.cosumaf_report_status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
