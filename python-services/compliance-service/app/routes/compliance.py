"""
Compliance API routes — compliance-service.

SaaS platform event logging, audit trail, and reporting.
All events use payment_routed/claim_forwarded terminology.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
import uuid
from defusedxml.ElementTree import Element, SubElement, tostring
from defusedxml import minidom

from app.core.database import get_db
from app.models.financial_event import FinancialEvent
from app.models.tax_exemption import TaxExemptionTracking

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


# ── Schemas ─────────────────────────────────────────────────────

class FinancialEventCreate(BaseModel):
    event_type: str  # payment_routed, claim_forwarded, saas_fee_received, tech_fee
    amount: int
    currency: str = "XOF"
    user_id: Optional[str] = None
    subscription_id: Optional[str] = None
    partner_id: Optional[str] = None
    provider: Optional[str] = None
    provider_ref: Optional[str] = None
    transaction_id: str


class FinancialEventResponse(BaseModel):
    id: str
    event_type: str
    amount: int
    transaction_id: str
    compliance_hash: str
    previous_hash: str
    routed_to_partner: Optional[bool] = None
    partner_id: Optional[str] = None
    wali_role: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Log Financial Event ─────────────────────────────────────────

@router.post("/events", response_model=FinancialEventResponse)
async def log_financial_event(
    event_data: FinancialEventCreate,
    db: Session = Depends(get_db),
):
    """Log a financial event with immutable hash chaining (SaaS model)."""
    try:
        last_event = db.query(FinancialEvent).order_by(FinancialEvent.created_at.desc()).first()
        previous_hash = last_event.compliance_hash if last_event else "0" * 64

        routed = event_data.event_type in ("payment_routed", "claim_forwarded")

        new_event = FinancialEvent(
            id=uuid.uuid4(),
            event_type=event_data.event_type,
            amount=event_data.amount,
            currency=event_data.currency,
            user_id=uuid.UUID(event_data.user_id) if event_data.user_id else None,
            subscription_id=uuid.UUID(event_data.subscription_id) if event_data.subscription_id else None,
            partner_id=event_data.partner_id,
            provider=event_data.provider,
            provider_ref=event_data.provider_ref,
            transaction_id=event_data.transaction_id,
            wali_role="technology_provider",
            previous_hash=previous_hash,
            routed_to_partner=routed,
        )
        new_event.compliance_hash = new_event.calculate_hash(previous_hash)

        db.add(new_event)

        # Update Tax Tracking
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1

        tracking = db.query(TaxExemptionTracking).filter_by(
            fiscal_year=current_year, quarter=current_quarter
        ).first()
        if not tracking:
            tracking = TaxExemptionTracking(fiscal_year=current_year, quarter=current_quarter)
            db.add(tracking)

        if event_data.event_type == "saas_fee_received":
            tracking.saas_subscription_revenue += event_data.amount
            tracking.taxable_revenue += event_data.amount
        elif event_data.event_type == "tech_fee":
            tracking.platform_service_revenue += event_data.amount
            tracking.taxable_revenue += event_data.amount
        elif event_data.event_type == "payment_routed":
            tracking.total_payments_routed += 1
            tracking.tax_exempt_revenue += event_data.amount  # Not Wali revenue
        elif event_data.event_type == "claim_forwarded":
            tracking.total_incidents_forwarded += 1

        db.commit()
        db.refresh(new_event)
        return FinancialEventResponse(**new_event.to_dict())

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ── Audit Trail ─────────────────────────────────────────────────

@router.get("/audit-trail", response_model=List[FinancialEventResponse])
async def get_audit_trail(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    provider: Optional[str] = None,
    event_type: Optional[str] = None,
    partner_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(FinancialEvent).order_by(FinancialEvent.created_at.desc())
    if start_date:
        query = query.filter(FinancialEvent.created_at >= start_date)
    if end_date:
        query = query.filter(FinancialEvent.created_at <= end_date)
    if provider:
        query = query.filter(FinancialEvent.provider == provider)
    if event_type:
        query = query.filter(FinancialEvent.event_type == event_type)
    if partner_id:
        query = query.filter(FinancialEvent.partner_id == partner_id)

    return [FinancialEventResponse(**e.to_dict()) for e in query.offset(skip).limit(limit).all()]


# ── Admin Stats ─────────────────────────────────────────────────

@router.get("/admin/payments/stats")
async def get_admin_payment_stats(db: Session = Depends(get_db)):
    """Payment routing statistics."""
    events = db.query(FinancialEvent).all()
    total_routed = sum(e.amount for e in events if e.event_type == "payment_routed")
    saas_revenue = sum(e.amount for e in events if e.event_type == "saas_fee_received")

    providers = {}
    for e in events:
        if e.event_type == "payment_routed":
            p = e.provider or "unknown"
            providers[p] = providers.get(p, 0) + e.amount

    return {
        "total_routed_to_partners": total_routed,
        "saas_subscription_revenue": saas_revenue,
        "provider_breakdown": providers,
        "wali_role": "technology_provider",
    }


@router.get("/admin/analytics")
async def get_admin_analytics(days: int = 30, db: Session = Depends(get_db)):
    """Time-series: payments routed and SaaS revenue."""
    from sqlalchemy import func
    from datetime import timedelta

    start_point = datetime.now() - timedelta(days=days)

    routed_data = db.query(
        func.date(FinancialEvent.created_at).label("date"),
        func.sum(FinancialEvent.amount).label("amount"),
    ).filter(
        FinancialEvent.created_at >= start_point,
        FinancialEvent.event_type == "payment_routed",
    ).group_by(func.date(FinancialEvent.created_at)).all()

    incidents_data = db.query(
        func.date(FinancialEvent.created_at).label("date"),
        func.count(FinancialEvent.id).label("count"),
    ).filter(
        FinancialEvent.created_at >= start_point,
        FinancialEvent.event_type == "claim_forwarded",
    ).group_by(func.date(FinancialEvent.created_at)).all()

    return {
        "payments_routed": [{"date": str(d.date), "amount": d.amount} for d in routed_data],
        "incidents_forwarded": [{"date": str(d.date), "count": d.count} for d in incidents_data],
        "wali_role": "technology_provider",
    }


# ── Compliance Stats ────────────────────────────────────────────

@router.get("/stats")
async def get_compliance_stats(db: Session = Depends(get_db)):
    """SaaS platform compliance statistics."""
    records = db.query(TaxExemptionTracking).all()

    total_saas = sum(r.saas_subscription_revenue for r in records)
    total_platform = sum(r.platform_service_revenue for r in records)
    total_routed = sum(r.total_payments_routed for r in records)
    total_incidents = sum(r.total_incidents_forwarded for r in records)

    return {
        "saas_subscription_revenue": total_saas,
        "platform_service_revenue": total_platform,
        "total_payments_routed_count": total_routed,
        "total_incidents_forwarded_count": total_incidents,
        "platform_model": "B2B_SAAS",
        "is_saas_platform": True,
        "months_elapsed": 14,
        "total_months": 36,
        "wali_role": "technology_provider",
    }


# ── Monthly Report ──────────────────────────────────────────────

@router.get("/reports/monthly")
async def generate_monthly_report(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    """Generate platform compliance report (SaaS model)."""
    from sqlalchemy import func

    year, month_num = map(int, month.split("-"))

    events = db.query(FinancialEvent).filter(
        func.extract("year", FinancialEvent.created_at) == year,
        func.extract("month", FinancialEvent.created_at) == month_num,
    ).all()

    total_routed = sum(e.amount for e in events if e.routed_to_partner)
    total_saas = sum(e.amount for e in events if e.event_type == "saas_fee_received")

    root = Element("PlatformReport")
    SubElement(root, "ReportDate").text = datetime.now().isoformat()
    SubElement(root, "Period").text = month
    SubElement(root, "PlatformModel").text = "B2B_SAAS"
    SubElement(root, "NAFCode").text = "6201Z"

    revenue = SubElement(root, "Revenue")
    SubElement(revenue, "SaaS_Subscription").text = str(total_saas)
    SubElement(revenue, "Payments_Routed_To_Partners").text = str(total_routed)

    transactions = SubElement(root, "Transactions")
    for e in events:
        txn = SubElement(transactions, "Transaction")
        txn.set("id", e.transaction_id)
        SubElement(txn, "Amount").text = str(e.amount)
        SubElement(txn, "Hash").text = e.compliance_hash
        SubElement(txn, "Type").text = e.event_type
        SubElement(txn, "RoutedToPartner").text = str(e.routed_to_partner)

    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
    return {"xml_content": xml_str, "status": "generated", "platform_model": "B2B_SAAS"}


# ── Chain Verification ──────────────────────────────────────────

@router.get("/verify-chain")
async def verify_chain_integrity(db: Session = Depends(get_db)):
    """Validate hash chain integrity."""
    events = db.query(FinancialEvent).order_by(FinancialEvent.created_at.asc()).all()
    broken_links = []

    previous_hash = "0" * 64
    for event in events:
        calculated = event.calculate_hash(previous_hash)
        if event.previous_hash != previous_hash:
            broken_links.append({"id": str(event.id), "reason": "Previous hash mismatch"})
        if event.compliance_hash != calculated:
            broken_links.append({"id": str(event.id), "reason": "Tampering detected"})
        previous_hash = event.compliance_hash

    if broken_links:
        return {"status": "compromised", "broken_links": broken_links}
    return {"status": "verified", "chain_length": len(events)}
