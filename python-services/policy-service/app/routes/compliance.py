from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field
import uuid
import hashlib
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from sqlalchemy import func

from app.core.database import get_db
from app.core.security_middleware import verify_admin
from app.models.financial_event import FinancialEvent
from app.models.tax_exemption import TaxExemptionTracking

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])

# Pydantic Models
class FinancialEventCreate(BaseModel):
    event_type: str
    amount: int
    currency: str = 'XOF'
    user_id: Optional[str] = None
    policy_id: Optional[str] = None
    provider: Optional[str] = None
    provider_ref: Optional[str] = None
    transaction_id: str

class FinancialEventResponse(BaseModel):
    id: str
    transaction_id: str
    amount: int
    compliance_hash: str
    previous_hash: str
    escrow_segregated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/events", response_model=FinancialEventResponse)
async def log_financial_event(
    event_data: FinancialEventCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Log a financial event with immutable hash chaining.
    """
    try:
        # Get last event for chaining
        last_event = db.query(FinancialEvent).order_by(FinancialEvent.created_at.desc()).first()
        previous_hash = last_event.compliance_hash if last_event else "0" * 64 # Genesis hash
        
        # Determine Escrow status
        escrow_segregated = event_data.event_type == 'premium_collected'
        
        # Create new event object
        new_event = FinancialEvent(
            id=uuid.uuid4(),
            event_type=event_data.event_type,
            amount=event_data.amount,
            currency=event_data.currency,
            user_id=uuid.UUID(event_data.user_id) if event_data.user_id else None,
            policy_id=uuid.UUID(event_data.policy_id) if event_data.policy_id else None,
            provider=event_data.provider,
            provider_ref=event_data.provider_ref,
            transaction_id=event_data.transaction_id,
            previous_hash=previous_hash,
            escrow_segregated=escrow_segregated
        )
        
        # Calculate Compliance Hash
        # Note: We need to set the values on the instance for the method to use them, 
        # or we pass them manually. The method uses self.transaction_id etc.
        new_event.compliance_hash = new_event.calculate_hash(previous_hash)
        
        db.add(new_event)
        
        # Update Tax Exemption Tracking (Naive implementation for MVP)
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1
        
        tracking = db.query(TaxExemptionTracking).filter_by(
            fiscal_year=current_year, 
            quarter=current_quarter
        ).first()
        
        if not tracking:
            tracking = TaxExemptionTracking(
                fiscal_year=current_year,
                quarter=current_quarter
            )
            db.add(tracking)
        
        if escrow_segregated:
            tracking.tax_exempt_revenue += event_data.amount
            tracking.total_premiums_collected += 1 # simplistic count
        else:
            tracking.taxable_revenue += event_data.amount
            
        db.commit()
        db.refresh(new_event)
        
        return FinancialEventResponse(**new_event.to_dict())

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-trail", response_model=List[FinancialEventResponse])
async def get_audit_trail(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    provider: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
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
    
    query = query.offset(skip).limit(limit)
    
    return [FinancialEventResponse(**e.to_dict()) for e in query.all()]

@router.get("/admin/payments/stats")
async def get_admin_payment_stats(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Summary metrics for the payments tab."""
    events = db.query(FinancialEvent).all()
    total_volume = sum(e.amount for e in events)
    success_rate = 100.0 if len(events) > 0 else 0.0 # Mocking for now
    
    # Provider breakdown
    providers = {}
    for e in events:
        p = e.provider or "unknown"
        providers[p] = providers.get(p, 0) + e.amount
        
    return {
        "total_volume": total_volume,
        "pending_volume": total_volume * 0.1, # Mocked
        "failed_volume": total_volume * 0.02, # Mocked
        "success_rate": success_rate,
        "provider_breakdown": providers
    }

@router.get("/admin/analytics")
async def get_admin_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Aggregated time-series data for analytics charts."""
    from sqlalchemy import func
    from datetime import timedelta
    
    start_point = datetime.now() - timedelta(days=days)
    
    # Revenue (Premiums Collected)
    revenue_data = db.query(
        func.date(FinancialEvent.created_at).label('date'),
        func.sum(FinancialEvent.amount).label('amount')
    ).filter(
        FinancialEvent.created_at >= start_point,
        FinancialEvent.event_type == 'premium_collected'
    ).group_by(func.date(FinancialEvent.created_at)).all()
    
    # Claims Paid
    claims_data = db.query(
        func.date(FinancialEvent.created_at).label('date'),
        func.sum(FinancialEvent.amount).label('amount')
    ).filter(
        FinancialEvent.created_at >= start_point,
        FinancialEvent.event_type == 'claim_payout'
    ).group_by(func.date(FinancialEvent.created_at)).all()
    
    return {
        "revenue": [{"date": str(d.date), "amount": d.amount} for d in revenue_data],
        "claims": [{"date": str(d.date), "amount": d.amount} for d in claims_data]
    }

@router.get("/stats")
async def get_compliance_stats(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get aggregated compliance statistics from TaxExemptionTracking
    """
    # Sum up all records to get total stats (life-to-date)
    tracking_records = db.query(TaxExemptionTracking).all()
    
    total_exempt = sum(r.tax_exempt_revenue for r in tracking_records)
    total_taxable = sum(r.taxable_revenue for r in tracking_records)
    total_premiums = sum(r.total_premiums_collected for r in tracking_records)
    total_claims = sum(r.total_claims_paid for r in tracking_records)
    
    # Calculate global loss ratio
    loss_ratio = 0.0
    if total_premiums > 0:
        loss_ratio = (float(total_claims) / float(total_premiums)) * 100
        
    return {
        "tax_exempt_revenue": total_exempt,
        "taxable_revenue": total_taxable,
        "total_premiums_collected": total_premiums,
        "total_claims_paid": total_claims,
        "loss_ratio": loss_ratio,
        "months_elapsed": 14, # Hardcoded for MVP as per requirements
        "total_months": 36    # Hardcoded for MVP
    }

@router.get("/reports/monthly")
async def generate_monthly_report(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Generate COSUMAF-compliant XML report
    """
    # Dummy XML generation logic for MVP
    year, month_num = map(int, month.split('-'))
    
    events = db.query(FinancialEvent).filter(
        func.extract('year', FinancialEvent.created_at) == year,
        func.extract('month', FinancialEvent.created_at) == month_num
    ).all()
    
    total_exempt = sum(e.amount for e in events if e.escrow_segregated)
    total_taxable = sum(e.amount for e in events if not e.escrow_segregated)
    
    # XML Construction
    root = Element('CosumafReport')
    SubElement(root, 'ReportDate').text = datetime.now().isoformat()
    SubElement(root, 'Period').text = month
    
    revenue = SubElement(root, 'Revenue_Segregation')
    SubElement(revenue, 'TaxExempt_Escrow').text = str(total_exempt)
    SubElement(revenue, 'Taxable_Operating').text = str(total_taxable)
    
    transactions = SubElement(root, 'Transactions')
    for e in events:
        txn = SubElement(transactions, 'Transaction')
        txn.set('id', e.transaction_id)
        SubElement(txn, 'Amount').text = str(e.amount)
        SubElement(txn, 'Hash').text = e.compliance_hash
        SubElement(txn, 'Type').text = e.event_type

    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
    
    return {"xml_content": xml_str, "status": "generated"}

@router.get("/verify-chain")
async def verify_chain_integrity(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Validate the entire hash chain
    """
    events = db.query(FinancialEvent).order_by(FinancialEvent.created_at.asc()).all()
    broken_links = []
    
    previous_hash = "0" * 64
    for event in events:
        # Re-calculate hash
        calculated = event.calculate_hash(previous_hash)
        
        if event.previous_hash != previous_hash:
             broken_links.append({"id": str(event.id), "reason": "Previous hash mismatch"})
        
        if event.compliance_hash != calculated:
             broken_links.append({"id": str(event.id), "reason": "Current hash mismatch (Tampering detected)"})
             
        previous_hash = event.compliance_hash
        
    if broken_links:
        return {"status": "compromised", "broken_links": broken_links}
        
    return {"status": "verified", "chain_length": len(events)}
