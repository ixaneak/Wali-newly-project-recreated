from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey, Enum, Text, Numeric, JSON
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class Partner(Base):
    __tablename__ = "partners"
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    license_number = Column(String(50))
    is_active = Column(Boolean, default=True)
    monthly_fee = Column(Integer, default=500_000)
    contract_start = Column(Date)
    contract_end = Column(Date)
    collection_account_id = Column(String(100))
    payout_account_id = Column(String(100))
    white_label_config = Column(JSON)
    api_rate_limit = Column(Integer, default=10_000)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PartnerInvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"

class PartnerInvoice(Base):
    __tablename__ = "partner_invoices"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String(50), ForeignKey("partners.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    amount_due = Column(Integer, nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0.18)
    total_with_tax = Column(Integer)
    description = Column(Text, default="Licence logicielle SaaS - Plateforme WALI")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(Enum(PartnerInvoiceStatus), default=PartnerInvoiceStatus.DRAFT)
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PlatformUsageLog(Base):
    __tablename__ = "platform_usage_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String(50), ForeignKey("partners.id"), nullable=False)
    log_date = Column(Date, nullable=False)
    api_calls_count = Column(Integer, default=0)
    active_artisans_count = Column(Integer, default=0)
    ussd_sessions_count = Column(Integer, default=0)
    whatsapp_interactions = Column(Integer, default=0)
    enrollments_processed = Column(Integer, default=0)
    incidents_reported = Column(Integer, default=0)
    platform_uptime_percent = Column(Numeric(5, 2), default=99.9)
    storage_gb_used = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PartnerApiConfig(Base):
    __tablename__ = "partner_api_configs"
    partner_id = Column(String(50), ForeignKey("partners.id"), primary_key=True)
    api_key = Column(String(255))
    webhook_url = Column(String(255))
    rate_limit = Column(Integer, default=10_000)
    allowed_endpoints = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
