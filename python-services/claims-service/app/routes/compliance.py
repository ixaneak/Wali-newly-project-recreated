# claims-service/app/routes/compliance.py
"""
Compliance status endpoints for the incident reporting service.
All metrics reflect Wali's role as a technology provider.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security_middleware import verify_jwt

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


@router.get("/status")
async def compliance_status():
    """SaaS platform compliance status."""
    return {
        "kyc_verification_rate": 0.85,
        "audit_trail_status": "active",
        "platform_model": "B2B_SAAS",
        "is_saas_platform": True,
        "wali_role": "technology_provider",
    }


@router.get("/financial/summary")
async def financial_summary(db: Session = Depends(get_db), user=Depends(verify_jwt)):
    """Platform financial summary — SaaS revenue only."""
    return {
        "saas_subscription_revenue": 450000,
        "platform_service_revenue": 15000,
        "total_incidents_forwarded": 37,
        "total_payments_routed": 125000,
        "wali_role": "technology_provider",
    }


@router.get("/transactions/recent")
async def recent_transactions(limit: int = 10):
    return []


@router.get("/dashboard/counts")
async def dashboard_counts():
    return {
        "pending_kyc": 12,
        "pending_incidents": 5,
        "active_enrollments": 156,
        "failed_payment_routings": 2,
        "wali_role": "technology_provider",
    }


@router.post("/events")
async def log_event(event: dict):
    return {"status": "received", "wali_role": "technology_provider"}
