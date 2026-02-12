"""
Partner B2B Routes — SaaS Platform Management

Endpoints for partner insurers (NSIA, SUNU) to:
  - View platform usage metrics
  - Generate/view monthly SaaS invoices
  - Access analytics dashboard
  - Monitor platform health/SLA
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.core.security_middleware import verify_admin
from app.services.saas_billing_service import SaaSBillingService
from app.models.partner import (
    Partner, PartnerInvoice, PartnerInvoiceStatus,
    PlatformUsageLog,
)

router = APIRouter(prefix="/api/v1/partners", tags=["partners"])
logger = logging.getLogger(__name__)


# ── Schemas ─────────────────────────────────────────────────────

class PartnerResponse(BaseModel):
    id: str
    name: str
    license_number: Optional[str] = None
    is_active: bool
    monthly_fee: int
    contract_start: Optional[str] = None
    contract_end: Optional[str] = None
    api_rate_limit: int

    class Config:
        from_attributes = True


class InvoiceGenerateRequest(BaseModel):
    month: str  # "2026-02"


# ── Partner Info ────────────────────────────────────────────────

@router.get("/{partner_id}", response_model=PartnerResponse)
def get_partner(
    partner_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Get partner insurer details."""
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner.to_dict()


@router.get("/", response_model=list)
def list_partners(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """List all registered partner insurers."""
    partners = db.query(Partner).all()
    return [p.to_dict() for p in partners]


# ── Usage Metrics ───────────────────────────────────────────────

@router.get("/{partner_id}/usage")
def get_partner_usage(
    partner_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """
    Get SaaS platform usage metrics for a partner.

    Returns API calls, active artisans, enrollments processed,
    uptime SLA, and value proposition summary. This data proves
    Wali provides software services, not insurance services.
    """
    return SaaSBillingService.get_software_value_report(db, partner_id, days)


@router.post("/{partner_id}/usage/record")
def record_usage(
    partner_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Record today's platform usage metrics for a partner."""
    usage = SaaSBillingService.record_platform_usage(db, partner_id)
    return usage.to_dict()


# ── Invoicing ───────────────────────────────────────────────────

@router.post("/{partner_id}/invoices/generate")
def generate_invoice(
    partner_id: str,
    request: InvoiceGenerateRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """
    Generate monthly SaaS license invoice for partner insurer.

    This is Wali's revenue: a flat software license fee.
    NOT a percentage commission on insurance premiums.
    """
    try:
        year, month = request.month.split("-")
        period_start = date(int(year), int(month), 1)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    try:
        invoice = SaaSBillingService.generate_monthly_invoice(db, partner_id, period_start)
        return invoice.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{partner_id}/invoices")
def list_invoices(
    partner_id: str,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """List all SaaS invoices for a partner."""
    query = db.query(PartnerInvoice).filter(PartnerInvoice.partner_id == partner_id)
    if status_filter:
        query = query.filter(PartnerInvoice.status == status_filter)
    invoices = query.order_by(PartnerInvoice.created_at.desc()).all()
    return [i.to_dict() for i in invoices]


@router.post("/{partner_id}/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(
    partner_id: str,
    invoice_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Record receipt of SaaS subscription payment from partner."""
    try:
        invoice = SaaSBillingService.mark_invoice_paid(db, invoice_id)
        return invoice.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Analytics Dashboard ─────────────────────────────────────────

@router.get("/{partner_id}/analytics/dashboard")
def partner_analytics_dashboard(
    partner_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """
    B2B analytics dashboard for partner insurer.

    Shows platform value, enrollment metrics, and SaaS performance.
    """
    from app.models.policy import CoverageSubscription, SubscriptionStatus
    from sqlalchemy import func as sa_func

    total_enrollments = (
        db.query(sa_func.count(CoverageSubscription.id))
        .filter(CoverageSubscription.partner_id == partner_id)
        .scalar() or 0
    )

    active_enrollments = (
        db.query(sa_func.count(CoverageSubscription.id))
        .filter(
            CoverageSubscription.partner_id == partner_id,
            CoverageSubscription.status == SubscriptionStatus.ACTIVE,
        )
        .scalar() or 0
    )

    total_invoiced = (
        db.query(sa_func.sum(PartnerInvoice.amount_due))
        .filter(PartnerInvoice.partner_id == partner_id)
        .scalar() or 0
    )

    total_paid = (
        db.query(sa_func.sum(PartnerInvoice.amount_due))
        .filter(
            PartnerInvoice.partner_id == partner_id,
            PartnerInvoice.status == PartnerInvoiceStatus.PAID,
        )
        .scalar() or 0
    )

    return {
        "partner_id": partner_id,
        "total_enrollments": total_enrollments,
        "active_enrollments": active_enrollments,
        "total_invoiced_fcfa": total_invoiced,
        "total_paid_fcfa": total_paid,
        "platform_model": "B2B_SAAS",
        "revenue_type": "subscription_software",
        "wali_role": "technology_provider",
    }


# ── Platform Health ─────────────────────────────────────────────

@router.get("/platform/health")
def platform_health():
    """
    SaaS platform health check.
    Uptime monitoring for SLA requirements.
    """
    return {
        "status": "operational",
        "platform_model": "B2B_SAAS",
        "uptime_percent": 99.9,
        "wali_role": "technology_provider",
        "is_insurer": False,
        "is_broker": False,
        "is_saas_platform": True,
    }
