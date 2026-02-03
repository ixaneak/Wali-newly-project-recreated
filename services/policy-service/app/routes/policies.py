"""Policy API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.models.policy import PolicyStatus, CoverageType, PaymentFrequency
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


# ==================== Pydantic Schemas ====================

class CoverageDetailsSchema(BaseModel):
    """Coverage details for policy."""
    max_coverage_amount: int = Field(..., gt=0, description="Maximum coverage in XOF")
    deductible: Optional[int] = Field(None, ge=0, description="Deductible amount in XOF")
    description: Optional[str] = None


class PolicyCreateRequest(BaseModel):
    """Request to create a new policy."""
    user_id: str
    coverage_type: CoverageType
    coverage_details: CoverageDetailsSchema
    payment_frequency: PaymentFrequency
    region: Optional[str] = None


class PolicyActivateRequest(BaseModel):
    """Request to activate a policy."""
    transaction_ref: str


class PolicyUpdatePaymentRequest(BaseModel):
    """Request to update policy payment."""
    transaction_ref: str


class PolicyCancelRequest(BaseModel):
    """Request to cancel a policy."""
    reason: str


class PolicyResponse(BaseModel):
    """Policy response."""
    id: str
    user_id: str
    policy_number: str
    coverage_type: str
    coverage_details: dict
    premium_amount: int
    payment_frequency: str
    status: str
    mobile_money_ref: Optional[str]
    last_payment_date: Optional[str]
    next_payment_date: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# ==================== Routes ====================

@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    request: PolicyCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new insurance policy.
    
    - **user_id**: UUID of the user
    - **coverage_type**: health, equipment, theft, or bundle
    - **coverage_details**: Coverage specifics including max_coverage_amount
    - **payment_frequency**: daily, weekly, or monthly
    - **region**: Optional region for risk calculation
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received policy creation request for user: {request.user_id}")
    try:
        print(f"DEBUG: Route received request for user {request.user_id}")
        policy = PolicyService.create_policy(
            db=db,
            user_id=request.user_id,
            coverage_type=request.coverage_type,
            coverage_details=request.coverage_details.model_dump(),
            payment_frequency=request.payment_frequency,
            region=request.region
        )
        return policy.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific policy by ID."""
    policy = PolicyService.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    return policy.to_dict()


@router.get("/user/{user_id}", response_model=List[PolicyResponse])
def get_user_policies(
    user_id: str,
    status_filter: Optional[PolicyStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all policies for a user, optionally filtered by status."""
    policies = PolicyService.get_user_policies(db, user_id, status_filter)
    return [p.to_dict() for p in policies]


@router.post("/{policy_id}/activate", response_model=PolicyResponse)
def activate_policy(
    policy_id: str,
    request: PolicyActivateRequest,
    db: Session = Depends(get_db)
):
    """
    Activate a policy after successful payment.
    
    This endpoint should be called by the payment service after confirming payment.
    """
    try:
        policy = PolicyService.activate_policy(
            db=db,
            policy_id=policy_id,
            transaction_ref=request.transaction_ref
        )
        return policy.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{policy_id}/payment", response_model=PolicyResponse)
def update_policy_payment(
    policy_id: str,
    request: PolicyUpdatePaymentRequest,
    db: Session = Depends(get_db)
):
    """Update policy after premium payment."""
    try:
        policy = PolicyService.update_policy_payment(
            db=db,
            policy_id=policy_id,
            transaction_ref=request.transaction_ref
        )
        return policy.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{policy_id}/cancel", response_model=PolicyResponse)
def cancel_policy(
    policy_id: str,
    request: PolicyCancelRequest,
    db: Session = Depends(get_db)
):
    """Cancel a policy."""
    try:
        policy = PolicyService.cancel_policy(
            db=db,
            policy_id=policy_id,
            reason=request.reason
        )
        return policy.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=List[PolicyResponse])
def list_all_policies(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[PolicyStatus] = None,
    db: Session = Depends(get_db)
):
    """
    List all policies (admin only).
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **status_filter**: Optional status filter
    """
    from app.models.policy import Policy
    
    query = db.query(Policy)
    
    if status_filter:
        query = query.filter(Policy.status == status_filter)
    
    policies = query.offset(skip).limit(limit).all()
    return [p.to_dict() for p in policies]


@router.get("/{policy_id}/certificate")
def get_policy_certificate(
    policy_id: str,
    db: Session = Depends(get_db)
):
    """Generate and download policy certificate."""
    from fastapi.responses import Response
    from app.services.pdf_service import generate_policy_certificate
    
    policy = PolicyService.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
        
    pdf_bytes = generate_policy_certificate(policy.to_dict())
    
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=policy_{policy.policy_number}.pdf"
        }
    )
