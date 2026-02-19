"""
Incident Report Routes (was: claims.py)

Manages incident reports filed by artisans and forwarded to partner insurers.
Wali does NOT process claims or make payouts — we forward incident reports
to the partner insurer who handles all decisions and payments.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.models.claim import IncidentStatus
from app.services.claims_service import IncidentReportService
from app.core.config import get_settings
from app.core.security_middleware import verify_jwt, verify_admin
from app.core.rate_limit import limiter

# SAR Detection for compliance
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'policy-service'))
from app.services.sar_detection_engine import SARDetectionEngine, DetectionRuleType

router = APIRouter(prefix="/api/v1/partners", tags=["incident-reports"])
settings = get_settings()
logger = logging.getLogger(__name__)


# ==================== Pydantic Schemas ====================

class IncidentReviewRequest(BaseModel):
    """Request to review an incident report before forwarding to partner."""
    reviewer_id: str
    forward_to_partner: bool  # was: approved
    partner_approved_amount: Optional[int] = None
    review_notes: Optional[str] = None


class IncidentForwardRequest(BaseModel):
    """Record that incident was forwarded to partner insurer."""
    partner_reference: str  # Partner's case/claim number


class IncidentCreateRequest(BaseModel):
    """Request to file an incident report (JSON with pre-uploaded photos)."""
    user_id: str
    subscription_id: str  # was: policy_id
    partner_id: str = "NSIA"
    incident_type: str  # Product ID from partner
    description: str
    reported_amount: int
    photos: List[str] = []
    incident_date: Optional[str] = None


class IncidentResponse(BaseModel):
    """Incident report response."""
    id: str
    user_id: str
    subscription_id: str
    partner_id: str
    incident_number: str
    incident_type: str
    description: str
    reported_amount: int
    partner_approved_amount: Optional[int] = None
    image_urls: Optional[List[str]] = None
    exif_data: Optional[dict] = None
    status: str
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None
    fraud_score: int = 0
    fraud_flags: Optional[dict] = None
    partner_reference: Optional[str] = None
    forwarded_to_partner_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    reviewed_at: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Routes ====================

@router.post(
    "/{partner_id}/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def submit_incident_report(
    partner_id: str,
    request: Request,
    user_id: str = Form(...),
    subscription_id: str = Form(...),
    incident_type: str = Form(...),
    description: str = Form(...),
    reported_amount: int = Form(..., gt=0),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """
    File an incident report for forwarding to partner insurer.

    Wali collects the report and evidence, then forwards to
    the partner insurer who makes all claim decisions.
    
    SAR Detection: Automatically checks for rapid claims and other
    fraud indicators for compliance purposes.
    """
    if len(images) == 0:
        raise HTTPException(status_code=400, detail="At least one image is required")
    if len(images) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images allowed")

    image_data_list = []
    for image_file in images:
        contents = await image_file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > settings.max_image_size_mb:
            raise HTTPException(status_code=400, detail=f"Image exceeds {settings.max_image_size_mb}MB limit")

        filename = image_file.filename or "image.jpg"
        extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if extension not in settings.allowed_image_extensions:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {settings.allowed_image_extensions}")

        image_data_list.append((contents, filename))

    try:
        # Submit the incident
        incident = IncidentReportService.submit_incident(
            db=db,
            user_id=user_id,
            subscription_id=subscription_id,
            partner_id=partner_id,
            incident_type=incident_type,
            description=description,
            reported_amount=reported_amount,
            images=image_data_list,
        )
        
        # ═════════════════════════════════════════════════════════════════
        # SAR DETECTION - Check for suspicious activity
        # ═════════════════════════════════════════════════════════════════
        try:
            # Import policy service to get policy details
            from app.core.database import get_db as get_policy_db
            
            # Get policy creation date from subscription_id
            # For now, we'll use mock data - in production, query policy service
            policy_created_at = datetime.now() - timedelta(days=30)  # Mock: policy created 30 days ago
            
            # Prepare data for SAR detection
            claim_data = {
                'id': str(incident.id),
                'policy_id': subscription_id,
                'user_id': user_id,
                'claim_date': datetime.now().isoformat(),
                'claim_amount': reported_amount,
                'description': description,
                'is_claim_analysis': True,
                'created_at': policy_created_at.isoformat(),  # Policy creation date
                'documents': [{'exif_data': {}}]  # Simplified - should extract actual EXIF
            }
            
            # Run SAR detection
            sar_engine = SARDetectionEngine(db)
            risk_event = await sar_engine.analyze_claim_submission(claim_data, {
                'id': subscription_id,
                'user_id': user_id,
                'created_at': policy_created_at.isoformat()
            })
            
            if risk_event:
                logger.warning(f"SAR Risk detected for incident {incident.id}: {risk_event.rule_type} (Score: {risk_event.risk_score})")
                
                # Store risk event in incident metadata
                incident.fraud_flags = incident.fraud_flags or {}
                incident.fraud_flags['sar_detection'] = risk_event.to_dict()
                incident.fraud_score = risk_event.risk_score
                db.commit()
                
                # If high risk, compliance team is already notified by SAR engine
                
        except Exception as e:
            # Don't block claim submission if SAR detection fails
            logger.error(f"SAR detection failed for incident {incident.id}: {e}")
        
        return incident.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit incident report: {str(e)}")


@router.post(
    "/{partner_id}/incidents/submit-json",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def submit_incident_json(
    partner_id: str,
    request: Request,
    incident_request: IncidentCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """
    Submit incident report via JSON with pre-uploaded photo URLs.
    Photos should already be uploaded via the photos endpoint.
    
    SAR Detection: Automatically checks for rapid claims and other
    fraud indicators for compliance purposes.
    """
    try:
        from app.models.claim import IncidentReport, IncidentStatus
        import uuid

        incident = IncidentReport(
            id=uuid.uuid4(),
            user_id=incident_request.user_id,
            subscription_id=uuid.UUID(incident_request.subscription_id),
            partner_id=partner_id,
            incident_type=incident_request.incident_type,
            description=incident_request.description,
            reported_amount=incident_request.reported_amount,
            image_urls=incident_request.photos,
            status=IncidentStatus.SUBMITTED,
            incident_number=f"INC-{uuid.uuid4().hex[:8].upper()}",
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        # ═════════════════════════════════════════════════════════════════
        # SAR DETECTION - Check for suspicious activity
        # ═════════════════════════════════════════════════════════════════
        try:
            # Get policy creation date from subscription_id
            # For now, we'll use mock data - in production, query policy service
            policy_created_at = datetime.now() - timedelta(days=30)  # Mock: policy created 30 days ago
            
            # Prepare data for SAR detection
            claim_data = {
                'id': str(incident.id),
                'policy_id': incident_request.subscription_id,
                'user_id': incident_request.user_id,
                'claim_date': datetime.now().isoformat(),
                'claim_amount': incident_request.reported_amount,
                'description': incident_request.description,
                'is_claim_analysis': True,
                'created_at': policy_created_at.isoformat(),  # Policy creation date
                'documents': [{'exif_data': {}}]  # Simplified - should extract actual EXIF
            }
            
            # Run SAR detection
            sar_engine = SARDetectionEngine(db)
            risk_event = await sar_engine.analyze_claim_submission(claim_data, {
                'id': incident_request.subscription_id,
                'user_id': incident_request.user_id,
                'created_at': policy_created_at.isoformat()
            })
            
            if risk_event:
                logger.warning(f"SAR Risk detected for incident {incident.id}: {risk_event.rule_type} (Score: {risk_event.risk_score})")
                
                # Store risk event in incident metadata
                incident.fraud_flags = incident.fraud_flags or {}
                incident.fraud_flags['sar_detection'] = risk_event.to_dict()
                incident.fraud_score = risk_event.risk_score
                db.commit()
                
        except Exception as e:
            # Don't block claim submission if SAR detection fails
            logger.error(f"SAR detection failed for incident {incident.id}: {e}")

        return incident.to_dict()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit incident report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit incident report: {str(e)}")


@router.get("/{partner_id}/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(
    partner_id: str,
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """Get a specific incident report."""
    incident = IncidentReportService.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return incident.to_dict()


@router.get("/{partner_id}/incidents/user/{user_id}", response_model=List[IncidentResponse])
def get_user_incidents(
    partner_id: str,
    user_id: str,
    status_filter: Optional[IncidentStatus] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """Get all incident reports for an artisan."""
    incidents = IncidentReportService.get_user_incidents(db, user_id, status_filter)
    return [i.to_dict() for i in incidents]


@router.post("/{partner_id}/incidents/{incident_id}/review", response_model=IncidentResponse)
def review_incident(
    partner_id: str,
    incident_id: str,
    request: IncidentReviewRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(verify_admin),
):
    """
    Review incident report before forwarding to partner insurer.

    If forward_to_partner=True, the incident is forwarded to the
    partner insurer who makes the final claim decision.
    """
    try:
        incident = IncidentReportService.review_incident(
            db=db,
            incident_id=incident_id,
            reviewer_id=request.reviewer_id,
            forward_to_partner=request.forward_to_partner,
            partner_approved_amount=request.partner_approved_amount,
            review_notes=request.review_notes,
        )
        return incident.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{partner_id}/incidents/{incident_id}/forward", response_model=IncidentResponse)
def forward_to_partner(
    partner_id: str,
    incident_id: str,
    request: IncidentForwardRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(verify_admin),
):
    """
    Record that this incident was forwarded to the partner insurer.

    The partner_reference is the claim/case number assigned by the
    partner insurer to track the incident on their side.
    """
    try:
        incident = IncidentReportService.forward_to_partner(
            db=db,
            incident_id=incident_id,
            partner_reference=request.partner_reference,
        )
        return incident.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{partner_id}/incidents", response_model=List[IncidentResponse])
def list_partner_incidents(
    partner_id: str,
    status_filter: Optional[IncidentStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(verify_admin),
):
    """List all incident reports for a partner (admin only)."""
    incidents = IncidentReportService.get_all_incidents(
        db=db,
        partner_id=partner_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return [i.to_dict() for i in incidents]


@router.get("/{partner_id}/incidents/admin/stats")
def get_incident_stats(
    partner_id: str,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(verify_admin),
):
    """Get incident report statistics for admin dashboard."""
    return IncidentReportService.get_admin_stats(db, partner_id)
