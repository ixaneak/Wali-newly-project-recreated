# claims-service/app/routes/compliance.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security_middleware import verify_jwt

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])

@router.get("/status")
async def compliance_status():
    return {
        "kyc_verification_rate": 0.85,
        "audit_trail_status": "active",
        "last_backup": "2024-01-15T10:00:00Z"
    }

@router.get("/financial/summary")
async def financial_summary(db: Session = Depends(get_db), user=Depends(verify_jwt)):
    # Mock data until you implement real compliance tables
    return {
        "total_premiums": 450000,
        "total_claims": 125000,
        "escrow_balance": 325000,
        "taxable_revenue": 15000,
        "loss_ratio": 0.28
    }

@router.get("/transactions/recent")
async def recent_transactions(limit: int = 10):
    return []  # Empty array for now

@router.get("/dashboard/counts")
async def dashboard_counts():
    return {
        "pending_kyc": 12,
        "pending_claims": 5,
        "active_policies": 156,
        "failed_payments": 2
    }

@router.post("/events")
async def log_event(event: dict):
    return {"status": "received"}
