"""Claims API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.claim import ClaimStatus, CoverageType
from app.services.claims_service import ClaimsService
from app.core.config import get_settings

router = APIRouter(prefix="/api/v1/claims", tags=["claims"])
settings = get_settings()


# ==================== Pydantic Schemas ====================

class ClaimReviewRequest(BaseModel):
    """Request to review a claim."""
    reviewer_id: str
    approved: bool
    approved_amount: Optional[int] = None
    review_notes: Optional[str] = None


class ClaimPayoutRequest(BaseModel):
    """Request to mark claim as paid."""
    transaction_id: str


class ClaimResponse(BaseModel):
    """Claim response."""
    id: str
    user_id: str
    policy_id: str
    claim_number: str
    claim_type: str
    description: str
    claimed_amount: int
    approved_amount: Optional[int]
    image_urls: Optional[List[str]]
    exif_data: Optional[dict]
    status: str
    reviewer_id: Optional[str]
    review_notes: Optional[str]
    fraud_score: int
    fraud_flags: Optional[dict]
    created_at: str
    updated_at: str
    reviewed_at: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== Routes ====================

@router.post("/", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def submit_claim(
    user_id: str = Form(...),
    policy_id: str = Form(...),
    claim_type: CoverageType = Form(...),
    description: str = Form(...),
    claimed_amount: int = Form(..., gt=0),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Submit a new insurance claim with images.
    
    - **user_id**: UUID of the user
    - **policy_id**: UUID of the policy
    - **claim_type**: health, equipment, theft, or bundle
    - **description**: Detailed description of the claim
    - **claimed_amount**: Amount claimed in XOF
    - **images**: Claim evidence photos (max 5MB each, .jpg/.png)
    """
    # Validate number of images
    if len(images) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image is required"
        )
    
    if len(images) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 images allowed per claim"
        )
    
    # Process images
    image_data_list = []
    for image_file in images:
        # Validate file size
        contents = await image_file.read()
        size_mb = len(contents) / (1024 * 1024)
        
        if size_mb > settings.max_image_size_mb:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image {image_file.filename} exceeds max size of {settings.max_image_size_mb}MB"
            )
        
        # Validate file extension
        filename = image_file.filename or "image.jpg"
        extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
        
        if extension not in settings.allowed_image_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {settings.allowed_image_extensions}"
            )
        
        image_data_list.append((contents, filename))
    
    # Submit claim
    try:
        claim = ClaimsService.submit_claim(
            db=db,
            user_id=user_id,
            policy_id=policy_id,
            claim_type=claim_type,
            description=description,
            claimed_amount=claimed_amount,
            images=image_data_list
        )
        return claim.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit claim: {str(e)}"
        )


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific claim by ID."""
    claim = ClaimsService.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )
    return claim.to_dict()


@router.get("/user/{user_id}", response_model=List[ClaimResponse])
def get_user_claims(
    user_id: str,
    status_filter: Optional[ClaimStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all claims for a user, optionally filtered by status."""
    claims = ClaimsService.get_user_claims(db, user_id, status_filter)
    return [c.to_dict() for c in claims]


@router.post("/{claim_id}/review", response_model=ClaimResponse)
def review_claim(
    claim_id: str,
    request: ClaimReviewRequest,
    db: Session = Depends(get_db)
):
    """
    Review a claim (admin only).
    
    - **approved**: true to approve, false to reject
    - **approved_amount**: Optional approved amount (defaults to claimed amount)
    - **review_notes**: Optional notes for the review
    """
    try:
        claim = ClaimsService.review_claim(
            db=db,
            claim_id=claim_id,
            reviewer_id=request.reviewer_id,
            approved=request.approved,
            approved_amount=request.approved_amount,
            review_notes=request.review_notes
        )
        return claim.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{claim_id}/payout", response_model=ClaimResponse)
def mark_claim_paid(
    claim_id: str,
    request: ClaimPayoutRequest,
    db: Session = Depends(get_db)
):
    """Mark claim as paid after payout transaction completes."""
    try:
        claim = ClaimsService.mark_claim_paid(
            db=db,
            claim_id=claim_id,
            transaction_id=request.transaction_id
        )
        return claim.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/admin/pending", response_model=List[ClaimResponse])
def get_pending_claims(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get pending claims for admin review (admin only).
    
    Claims are sorted by fraud score (highest first) then by submission date.
    """
    claims = ClaimsService.get_pending_claims(db, limit)
    return [c.to_dict() for c in claims]
