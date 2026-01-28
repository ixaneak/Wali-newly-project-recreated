"""Compliance API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict

from app.core.database import get_db
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


# ==================== Pydantic Schemas ====================

class FinancialEventRequest(BaseModel):
    """Request to create a financial event."""
    event_type: str  # premium_collected, claim_paid, tech_fee, refund
    amount: int
    segregated_escrow: bool
    transaction_id: str = None
    policy_id: str = None
    claim_id: str = None
    user_id: str = None
    metadata: Dict = None


# ==================== Routes ====================

@router.post("/financial-events", status_code=status.HTTP_201_CREATED)
def create_financial_event(
    request: FinancialEventRequest,
    db: Session = Depends(get_db)
):
    """
    Create an immutable financial event in the audit trail.
    
    - **event_type**: premium_collected, claim_paid, tech_fee, refund
    - **amount**: Amount in XOF
    - **segregated_escrow**: true for premiums (escrow), false for tech fees
    """
    try:
        event = ComplianceService.create_financial_event(
            db=db,
            event_type=request.event_type,
            amount=request.amount,
            segregated_escrow=request.segregated_escrow,
            transaction_id=request.transaction_id,
            policy_id=request.policy_id,
            claim_id=request.claim_id,
            user_id=request.user_id,
            metadata=request.metadata
        )
        return event
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create financial event: {str(e)}"
        )


@router.get("/verify-hash-chain")
def verify_hash_chain(db: Session = Depends(get_db)):
    """
    Verify the integrity of the financial events hash chain.
    
    Returns validation status and any broken links detected.
    """
    return ComplianceService.verify_hash_chain(db)


@router.get("/reports/monthly/{year}/{month}", response_class=Response)
def generate_monthly_report(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """
    Generate COSUMAF-compliant monthly XML report.
    
    - **year**: Report year (e.g., 2026)
    - **month**: Report month (1-12)
    
    Returns XML document in UEMOA format.
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    try:
        xml_report = ComplianceService.generate_cosumaf_monthly_report(
            db=db,
            year=year,
            month=month
        )
        
        return Response(
            content=xml_report,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=COSUMAF_Report_{year}_{month:02d}.xml"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/tax-exemption-status")
def get_tax_exemption_status(
    start_date: str = "2026-01-01",
    db: Session = Depends(get_db)
):
    """
    Get 3-year tax exemption countdown and revenue segregation status.
    
    - **start_date**: Tax exemption start date (ISO format)
    
    Returns days remaining, revenue breakdown, and compliance status.
    """
    try:
        return ComplianceService.get_tax_exemption_status(db, start_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tax status: {str(e)}"
        )


@router.get("/revenue-segregation")
def get_revenue_segregation(db: Session = Depends(get_db)):
    """
    Get revenue breakdown between escrow (insurance premiums) and operating (tech fees).
    
    Critical for maintaining 3-year fintech tax exemption.
    """
    status = ComplianceService.get_tax_exemption_status(db)
    
    escrow_total = status["escrow_revenue_total"]
    operating_total = status["operating_revenue_total"]
    total_revenue = escrow_total + operating_total
    
    return {
        "escrow_account": {
            "total": escrow_total,
            "percentage": round((escrow_total / total_revenue * 100) if total_revenue > 0 else 0, 2),
            "description": "Insurance premiums (tax-exempt)"
        },
        "operating_account": {
            "total": operating_total,
            "percentage": round((operating_total / total_revenue * 100) if total_revenue > 0 else 0, 2),
            "description": "Tech fees (taxable at 2%)"
        },
        "total_revenue": total_revenue,
        "currency": "XOF"
    }
