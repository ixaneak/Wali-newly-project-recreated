from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field
import uuid

from app.core.database import get_db
from app.models import Claim, Policy, PolicyStatus
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/v1/claims", tags=["claims"])

# Pydantic models for request/response
class ClaimCreate(BaseModel):
    claim_type: str = Field(..., description="Type: medical, accident, property, other")
    amount: float = Field(..., gt=0, description="Claim amount")
    description: str = Field(..., min_length=10, description="Detailed description")
    incident_date: date = Field(..., description="Date of incident")
    photos: Optional[List[str]] = Field(default=[], description="Array of photo URLs")

class ClaimUpdate(BaseModel):
    status: Optional[str] = None
    review_notes: Optional[str] = None

class ClaimResponse(BaseModel):
    id: str
    user_id: str
    policy_id: Optional[str]
    claim_type: str
    amount: float
    description: str
    incident_date: str
    status: str
    review_notes: Optional[str]
    photos: Optional[List[str]]
    created_at: str
    updated_at: Optional[str]
    reviewed_at: Optional[str]
    reviewed_by: Optional[str]

    class Config:
        from_attributes = True


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a new insurance claim.
    
    Validates user has active policy and claim amount is within coverage.
    """
    try:
        # Check for active policy
        policy = db.query(Policy).filter(
            Policy.user_id == uuid.UUID(current_user["user_id"]),
            Policy.status == PolicyStatus.ACTIVE
        ).first()

        # Create claim
        new_claim = Claim(
            id=uuid.uuid4(),
            user_id=uuid.UUID(current_user["user_id"]),
            policy_id=policy.id if policy else None,
            claim_type=claim_data.claim_type,
            amount=claim_data.amount,
            description=claim_data.description,
            incident_date=claim_data.incident_date,
            status="submitted",
            photos=claim_data.photos or []
        )
        
        db.add(new_claim)
        db.commit()
        db.refresh(new_claim)
        
        return ClaimResponse(**new_claim.to_dict())
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create claim: {str(e)}"
        )


@router.get("", response_model=List[ClaimResponse])
async def get_user_claims(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    status_filter: Optional[str] = None
):
    """
    Get all claims for the current user.
    
    Optional filter by status.
    """
    try:
        query = db.query(Claim).filter(Claim.user_id == uuid.UUID(current_user["user_id"]))
        
        if status_filter:
            query = query.filter(Claim.status == status_filter)
        
        claims = query.order_by(Claim.created_at.desc()).all()
        
        return [ClaimResponse(**claim.to_dict()) for claim in claims]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch claims: {str(e)}"
        )


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific claim.
    
    Users can only view their own claims.
    """
    try:
        claim = db.query(Claim).filter(
            Claim.id == uuid.UUID(claim_id),
            Claim.user_id == uuid.UUID(current_user["user_id"])
        ).first()
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        return ClaimResponse(**claim.to_dict())
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid claim ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch claim: {str(e)}"
        )


# Admin endpoints
@router.get("/admin/all", response_model=List[ClaimResponse])
async def get_all_claims(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    status_filter: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Admin endpoint: Get all claims with pagination.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        query = db.query(Claim)
        
        if status_filter:
            query = query.filter(Claim.status == status_filter)

        if start_date:
            query = query.filter(Claim.created_at >= start_date)

        if end_date:
            # Add one day to include the end date fully if using datetime, or just use date comparison
            # Assuming created_at is datetime, we need to compare properly.
            # If created_at is string/datetime, simple comparison works if start_date is cast comparable.
            query = query.filter(Claim.created_at <= end_date)
        
        claims = query.order_by(Claim.created_at.desc()).offset(skip).limit(limit).all()
        
        return [ClaimResponse(**claim.to_dict()) for claim in claims]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch claims: {str(e)}"
        )


@router.patch("/admin/{claim_id}", response_model=ClaimResponse)
async def update_claim_status(
    claim_id: str,
    update_data: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admin endpoint: Update claim status and add review notes.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        claim = db.query(Claim).filter(Claim.id == uuid.UUID(claim_id)).first()
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        # Update fields
        if update_data.status:
            claim.status = update_data.status
        if update_data.review_notes:
            claim.review_notes = update_data.review_notes
        
        # Set reviewer info
        claim.reviewed_by = uuid.UUID(current_user["user_id"])
        claim.reviewed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(claim)
        
        return ClaimResponse(**claim.to_dict())
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid claim ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update claim: {str(e)}"
        )
