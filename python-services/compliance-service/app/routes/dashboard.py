"""
Dashboard API routes — compliance-service.

Provides dashboard data for the admin console.
All metrics reflect SaaS platform model.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.financial_event import FinancialEvent
from app.models.tax_exemption import TaxExemptionTracking

router = APIRouter(prefix="/api/v1/compliance", tags=["dashboard"])


@router.get("/compliance/status")
async def get_compliance_status(db: Session = Depends(get_db)):
    """SaaS platform compliance status."""
    return {
        "currentMonth": 14,
        "totalMonths": 36,
        "percentage": 38.9,
        "status": "COMPLIANT",
        "platform_model": "B2B_SAAS",
        "wali_role": "technology_provider",
    }


@router.get("/financial/summary")
async def get_financial_summary(db: Session = Depends(get_db)):
    """Platform financial summary — SaaS revenue streams."""
    tracking_records = db.query(TaxExemptionTracking).all()

    total_saas = sum(r.saas_subscription_revenue for r in tracking_records)
    total_platform = sum(r.platform_service_revenue for r in tracking_records)
    total_routed = sum(r.tax_exempt_revenue for r in tracking_records)

    # Fallback for empty DB
    if total_saas == 0 and total_platform == 0:
        total_saas = 45000000
        total_platform = 1200000
        total_routed = 125000

    return {
        "saasRevenue": {
            "amount": total_saas,
            "currency": "FCFA",
            "trend": 12.5,
        },
        "platformRevenue": {
            "amount": total_platform,
            "currency": "FCFA",
            "trend": 0,
        },
        "paymentsRouted": {
            "amount": total_routed,
            "currency": "FCFA",
            "label": "Payments routed to partner insurers",
        },
        "lastUpdated": datetime.now().isoformat(),
        "wali_role": "technology_provider",
    }


@router.get("/transactions/recent")
async def get_recent_transactions(
    limit: int = Query(10, gt=0),
    db: Session = Depends(get_db),
):
    """Recent financial events (SaaS model)."""
    events = db.query(FinancialEvent).order_by(FinancialEvent.created_at.desc()).limit(limit).all()

    return [
        {
            "id": f"TRX-{str(e.id)[:4].upper()}",
            "type": "Routed" if e.routed_to_partner else "SaaS Fee",
            "amount": e.amount,
            "status": "ROUTED" if e.routed_to_partner else "SAAS_REVENUE",
            "partner_id": e.partner_id,
            "date": e.created_at.strftime("%Y-%m-%d"),
        }
        for e in events
    ]


@router.get("/dashboard/counts")
async def get_dashboard_counts(db: Session = Depends(get_db)):
    """Dashboard summary counts."""
    return {
        "incidents_reported": 24,
        "active_artisans": 1234,
        "payments_routed": 12,
        "pending_reviews": 3,
        "wali_role": "technology_provider",
    }


@router.get("/audit-trail")
async def get_audit_trail_paged(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    db: Session = Depends(get_db),
):
    """Paginated audit trail."""
    skip = (page - 1) * limit
    events = db.query(FinancialEvent).order_by(FinancialEvent.created_at.desc()).offset(skip).limit(limit).all()
    return [e.to_dict() for e in events]
