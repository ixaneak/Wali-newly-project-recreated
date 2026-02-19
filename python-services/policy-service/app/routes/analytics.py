"""
Admin Unified Financial Analytics Routes

Combines platform-wide data from:
- Insurance premiums (cotisations)
- Pharmacy ecosystem (SaaS fees + reimbursements)  
- Claims payouts (sinistres)
- User transactions

Provides comprehensive financial overview for platform management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from datetime import datetime, date, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security_middleware_v2 import verify_admin

router = APIRouter(prefix="/api/v1/analytics", tags=["admin-financial-analytics"])


# ═════════════════════════════════════════════════════════════════
# ADMIN ANALYTICS SCHEMAS
# ═════════════════════════════════════════════════════════════════

class AdminPlatformMetrics(BaseModel):
    """Platform-wide financial metrics for admin dashboard."""
    total_revenue: int
    total_payouts: int
    net_position: int
    active_users: int
    total_transactions: int


class AdminRevenueBreakdown(BaseModel):
    premiums: int
    pharmacy_fees: int
    other_revenue: int


class AdminPayoutBreakdown(BaseModel):
    claim_payouts: int
    pharmacy_reimbursements: int
    refunds: int


class AdminPharmacyMetrics(BaseModel):
    active_pharmacies: int
    total_pharmacy_revenue: int
    avg_transaction_value: float


class AdminClaimsMetrics(BaseModel):
    total_submitted: int
    total_approved: int
    total_rejected: int
    avg_payout_amount: float
    approval_rate: float


class AdminTimeSeriesPoint(BaseModel):
    date: str
    label: str
    premiums: int
    claim_payouts: int
    pharmacy_revenue: int
    net_position: int
    transaction_count: int


class AdminUnifiedAnalyticsResponse(BaseModel):
    """Complete admin analytics combining all data sources."""
    platform: AdminPlatformMetrics
    revenue_by_source: AdminRevenueBreakdown
    payouts: AdminPayoutBreakdown
    pharmacy_metrics: AdminPharmacyMetrics
    claims_metrics: AdminClaimsMetrics
    time_series: List[AdminTimeSeriesPoint]
    category_distribution: List[dict]


# ═════════════════════════════════════════════════════════════════
# MOCK DATA GENERATOR
# ═════════════════════════════════════════════════════════════════

def generate_admin_mock_analytics(timeframe: str = '30D') -> dict:
    """Generate comprehensive admin analytics with all data sources."""
    days = {'7D': 7, '30D': 30, '90D': 90, '1Y': 365}.get(timeframe, 30)
    
    # Generate time series
    time_series = []
    for i in range(days - 1, -1, -1):
        dt = datetime.now() - timedelta(days=i)
        is_weekend = dt.weekday() >= 5
        
        base_premium = 250000 if not is_weekend else 50000
        base_payout = 450000 if not is_weekend else 100000
        base_pharmacy = 380000 if not is_weekend else 75000
        
        variance = 0.2
        premiums = int(base_premium * (1 + (hash(dt.isoformat()) % 100 - 50) / 250))
        payouts = int(base_payout * (1 + (hash(dt.isoformat() + 'p') % 100 - 50) / 250))
        pharmacy_rev = int(base_pharmacy * (1 + (hash(dt.isoformat() + 'ph') % 100 - 50) / 250))
        
        time_series.append({
            "date": dt.strftime("%Y-%m-%d"),
            "label": dt.strftime("%d %b"),
            "premiums": premiums,
            "claim_payouts": payouts,
            "pharmacy_revenue": pharmacy_rev,
            "net_position": premiums + int(pharmacy_rev * 0.15) - payouts,
            "transaction_count": 30 + (hash(dt.isoformat()) % 40)
        })
    
    total_premiums = sum(d["premiums"] for d in time_series)
    total_payouts = sum(d["claim_payouts"] for d in time_series)
    total_pharmacy = sum(d["pharmacy_revenue"] for d in time_series)
    
    return {
        "platform": {
            "total_revenue": total_premiums + int(total_pharmacy * 0.15) + 1250000,
            "total_payouts": total_payouts + int(total_pharmacy * 0.85) + 450000,
            "net_position": (total_premiums + int(total_pharmacy * 0.15)) - (total_payouts + int(total_pharmacy * 0.85)),
            "active_users": 2847,
            "total_transactions": sum(d["transaction_count"] for d in time_series)
        },
        "revenue_by_source": {
            "premiums": total_premiums,
            "pharmacy_fees": int(total_pharmacy * 0.15),
            "other_revenue": 1250000
        },
        "payouts": {
            "claim_payouts": total_payouts,
            "pharmacy_reimbursements": int(total_pharmacy * 0.85),
            "refunds": 450000
        },
        "pharmacy_metrics": {
            "active_pharmacies": 47,
            "total_pharmacy_revenue": total_pharmacy,
            "avg_transaction_value": 8750.0,
            "top_pharmacies": [
                {"id": "p1", "name": "Pharmacie Ivoire Santé - Cocody", "revenue": 2845000, "transactions": 342, "location": "Cocody", "growth": 12.5},
                {"id": "p2", "name": "Pharmacie de la Paix - Plateau", "revenue": 2150000, "transactions": 268, "location": "Plateau", "growth": 8.3},
                {"id": "p3", "name": "Grande Pharmacie d'Abidjan", "revenue": 1890000, "transactions": 221, "location": "Treichville", "growth": -2.1},
                {"id": "p4", "name": "Pharmacie du Centre - Marcory", "revenue": 1650000, "transactions": 198, "location": "Marcory", "growth": 15.7},
                {"id": "p5", "name": "Pharmacie Riviera Bonoumin", "revenue": 1420000, "transactions": 175, "location": "Riviera", "growth": 5.2},
            ]
        },
        "claims_metrics": {
            "total_submitted": 156,
            "total_approved": 124,
            "total_rejected": 32,
            "avg_payout_amount": 125000.0,
            "approval_rate": 79.5
        },
        "time_series": time_series,
        "category_distribution": [
            {"name": "Primes Assurance", "value": total_premiums, "color": "#0ea5e9"},
            {"name": "Frais Pharmacies", "value": int(total_pharmacy * 0.15), "color": "#6366f1"},
            {"name": "Remb. Sinistres", "value": total_payouts, "color": "#10b981"},
            {"name": "Remb. Pharmacies", "value": int(total_pharmacy * 0.85), "color": "#8b5cf6"},
            {"name": "Autres Revenus", "value": 1250000, "color": "#f59e0b"},
        ]
    }


# ═════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ═════════════════════════════════════════════════════════════════

@router.get("/admin/unified", response_model=AdminUnifiedAnalyticsResponse)
async def get_admin_unified_analytics(
    timeframe: Literal['7D', '30D', '90D', '1Y'] = Query(default='30D'),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get unified financial analytics for admin dashboard.
    
    Combines platform-wide data from:
    - Insurance premiums (cotisations)
    - Pharmacy ecosystem (SaaS fees + reimbursements)
    - Claims payouts (sinistres)
    - User transactions
    
    Returns comprehensive financial overview for platform management.
    """
    return generate_admin_mock_analytics(timeframe)


@router.get("/admin/summary")
async def get_admin_financial_summary(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Get quick financial summary for admin dashboard."""
    analytics = generate_admin_mock_analytics('30D')
    return {
        "revenue": analytics["platform"]["total_revenue"],
        "payouts": analytics["platform"]["total_payouts"],
        "net_position": analytics["platform"]["net_position"],
        "active_users": analytics["platform"]["active_users"],
        "active_pharmacies": analytics["pharmacy_metrics"]["active_pharmacies"],
        "claims_approval_rate": analytics["claims_metrics"]["approval_rate"]
    }
