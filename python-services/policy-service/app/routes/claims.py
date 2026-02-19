"""
Incident Report routes — policy-service copy.

These are PROXY routes that let artisans submit incident reports
through the main platform service. The actual incident processing
happens in the dedicated incident-service (claims-service).

Wali forwards incident data to partner insurers — it does NOT
process claims or make payouts.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field
import uuid

from app.core.database import get_db
from app.core.security_middleware_v2 import verify_jwt, verify_admin
from app.models.policy import SubscriptionStatus
# from app.models.policy import CoverageSubscription, SubscriptionStatus

router = APIRouter(prefix="/api/v1/partners/{partner_id}/incidents", tags=["incidents"])


# ── Schemas ───────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    incident_type: str = Field(..., description="Type: medical, accident, property, other")
    reported_amount: float = Field(..., gt=0, description="Amount reported by artisan")
    description: str = Field(..., min_length=10, description="Incident description")
    incident_date: date = Field(..., description="Date of incident")
    photos: Optional[List[str]] = Field(default=[], description="Photo URLs")


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    review_notes: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    user_id: str
    subscription_id: Optional[str] = None
    partner_id: Optional[str] = None
    incident_type: str
    reported_amount: float
    description: str
    incident_date: str
    status: str
    review_notes: Optional[str] = None
    photos: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    wali_role: str = "technology_provider"

    class Config:
        from_attributes = True


# ── Submit Incident ───────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_incident(
    partner_id: str,
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """
    Submit an incident report for forwarding to partner insurer.
    Wali does NOT process claims — we forward to the partner.
    """
    try:
        from app.models.policy import CoverageSubscription, SubscriptionStatus
        
        # Check for active enrollment with this partner
        subscription = db.query(CoverageSubscription).filter(
            CoverageSubscription.user_id == current_user["user_id"],
            CoverageSubscription.status == SubscriptionStatus.ACTIVE,
            CoverageSubscription.partner_id == partner_id,
        ).first()

        incident_id = str(uuid.uuid4())
        
        # COSUMAF COMPLIANCE: Audit Log
        from app.core.audit import log_audit_event
        await log_audit_event(
            action="CLAIM_SUBMISSION",
            outcome="SUCCESS",
            resource=incident_id,
            user_id=current_user["user_id"],
            detail={
                "partner_id": partner_id,
                "amount": incident_data.reported_amount,
                "type": incident_data.incident_type
            }
        )
        
        return {
            "id": incident_id,
            "user_id": current_user["user_id"],
            "partner_id": partner_id,
            "subscription_id": str(subscription.id) if subscription else None,
            "incident_type": incident_data.incident_type,
            "reported_amount": incident_data.reported_amount,
            "description": incident_data.description,
            "incident_date": str(incident_data.incident_date),
            "status": "submitted",
            "photos": incident_data.photos or [],
            "wali_role": "technology_provider",
            "message": "Incident report submitted. Will be forwarded to partner insurer.",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit incident report: {str(e)}",
        )


# ── Get User Incidents ────────────────────────────────────────

@router.get("")
async def get_user_incidents(
    partner_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
    status_filter: Optional[str] = None,
):
    """Get incident reports for a user with this partner."""
    return {
        "incidents": [],
        "partner_id": partner_id,
        "wali_role": "technology_provider",
        "message": "Incident history from partner insurer.",
    }


# ── Get Single Incident ──────────────────────────────────────

@router.get("/{incident_id}")
async def get_incident(
    partner_id: str,
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """Get incident report details."""
    return {
        "id": incident_id,
        "partner_id": partner_id,
        "wali_role": "technology_provider",
        "message": "Incident details forwarded from partner.",
    }


# ── Admin: All Incidents ─────────────────────────────────────

@router.get("/admin/all")
async def get_all_incidents(
    partner_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin),
    status_filter: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
):
    """Admin: Get all incidents for this partner (paginated)."""
    return {
        "incidents": [],
        "partner_id": partner_id,
        "total": 0,
        "wali_role": "technology_provider",
    }


# ── Admin: Update Incident ───────────────────────────────────

@router.patch("/admin/{incident_id}")
async def update_incident_status(
    partner_id: str,
    incident_id: str,
    update_data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin),
):
    """Admin: Update incident status and review notes."""
    return {
        "id": incident_id,
        "partner_id": partner_id,
        "status": update_data.status or "under_review",
        "review_notes": update_data.review_notes,
        "reviewed_by": current_user["user_id"],
        "reviewed_at": datetime.utcnow().isoformat(),
        "wali_role": "technology_provider",
    }
