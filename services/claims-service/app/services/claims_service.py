"""Claims service business logic."""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import logging

from app.models.claim import Claim, ClaimStatus, CoverageType
from app.core.storage import minio_client
from app.validators.exif_validator import EXIFValidator
from app.validators.fraud_detector import FraudDetector

logger = logging.getLogger(__name__)


class ClaimsService:
    """Service for managing insurance claims."""
    
    @staticmethod
    def submit_claim(
        db: Session,
        user_id: str,
        policy_id: str,
        claim_type: CoverageType,
        description: str,
        claimed_amount: int,
        images: List[tuple[bytes, str]]  # List of (image_data, filename)
    ) -> Claim:
        """
        Submit a new insurance claim with images.
        
        Args:
            db: Database session
            user_id: User UUID
            policy_id: Policy UUID
            claim_type: Type of claim
            description: Claim description
            claimed_amount: Amount claimed in XOF
            images: List of image data tuples
        
        Returns:
            Created Claim object
        """
        # Create claim record
        claim = Claim(
            user_id=user_id,
            policy_id=policy_id,
            claim_type=claim_type,
            description=description,
            claimed_amount=claimed_amount,
            status=ClaimStatus.SUBMITTED
        )
        
        db.add(claim)
        db.flush()  # Get claim ID
        
        claim_id = str(claim.id)
        image_urls = []
        image_hashes = []
        exif_data_list = []
        fraud_matches_all = []
        
        # Process each image
        for image_data, filename in images:
            # Validate EXIF metadata
            exif_result = EXIFValidator.validate_image(image_data)
            
            if not exif_result["valid"]:
                logger.warning(f"EXIF validation failed for claim {claim_id}: {exif_result['errors']}")
                # Store errors but don't reject automatically
                exif_data_list.append({
                    "filename": filename,
                    "valid": False,
                    "errors": exif_result["errors"]
                })
            else:
                exif_data_list.append({
                    "filename": filename,
                    "valid": True,
                    "data": exif_result["exif_data"]
                })
            
            # Calculate perceptual hash for fraud detection
            try:
                phash = FraudDetector.calculate_phash(image_data)
                image_hashes.append(phash)
                
                # Check for duplicate images
                matches = FraudDetector.check_duplicate_images(
                    db, phash, user_id, exclude_claim_id=claim_id
                )
                
                if matches:
                    fraud_matches_all.extend(matches)
                    logger.warning(f"Found {len(matches)} similar images for claim {claim_id}")
                
            except Exception as e:
                logger.error(f"Fraud detection failed for image: {e}")
                image_hashes.append(None)
            
            # Upload to MinIO
            file_extension = "." + filename.split(".")[-1] if "." in filename else ".jpg"
            try:
                object_name = minio_client.upload_image(image_data, claim_id, file_extension)
                
                # Generate presigned URL (24h expiry)
                presigned_url = minio_client.get_presigned_url(object_name)
                image_urls.append(presigned_url)
            except Exception as e:
                logger.error(f"Image upload failed: {e}")
                raise ValueError(f"Failed to upload image: {str(e)}")
        
        # Analyze fraud patterns
        fraud_analysis = FraudDetector.detect_fraud_patterns(fraud_matches_all)
        
        # Calculate fraud score (0-100)
        fraud_score = 0
        if fraud_analysis["fraud_detected"]:
            if fraud_analysis["risk_level"] == "critical":
                fraud_score = 95
            elif fraud_analysis["risk_level"] == "high":
                fraud_score = 75
            elif fraud_analysis["risk_level"] == "medium":
                fraud_score = 50
        
        # Update claim with processed data
        claim.image_urls = image_urls
        claim.image_hashes = [h for h in image_hashes if h is not None]
        claim.exif_data = {"images": exif_data_list}
        claim.fraud_score = fraud_score
        claim.fraud_flags = fraud_analysis
        
        # Auto-flag for review if fraud detected
        if fraud_analysis["fraud_detected"]:
            claim.status = ClaimStatus.UNDER_REVIEW
            logger.warning(f"Claim {claim_id} flagged for fraud review: {fraud_analysis['patterns']}")
        
        db.commit()
        db.refresh(claim)
        
        return claim
    
    @staticmethod
    def get_claim(db: Session, claim_id: str) -> Optional[Claim]:
        """Get a single claim by ID."""
        return db.query(Claim).filter(Claim.id == claim_id).first()
    
    @staticmethod
    def get_user_claims(
        db: Session, 
        user_id: str, 
        status: Optional[ClaimStatus] = None
    ) -> List[Claim]:
        """Get all claims for a user."""
        query = db.query(Claim).filter(Claim.user_id == user_id)
        
        if status:
            query = query.filter(Claim.status == status)
        
        return query.order_by(Claim.created_at.desc()).all()
    
    @staticmethod
    def review_claim(
        db: Session,
        claim_id: str,
        reviewer_id: str,
        approved: bool,
        approved_amount: Optional[int] = None,
        review_notes: Optional[str] = None
    ) -> Claim:
        """Admin review of a claim."""
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError("Claim not found")
        
        claim.reviewer_id = reviewer_id
        claim.review_notes = review_notes
        claim.reviewed_at = datetime.now()
        
        if approved:
            claim.status = ClaimStatus.APPROVED
            claim.approved_amount = approved_amount or claim.claimed_amount
        else:
            claim.status = ClaimStatus.REJECTED
        
        db.commit()
        db.refresh(claim)
        
        return claim
    
    @staticmethod
    def mark_claim_paid(
        db: Session,
        claim_id: str,
        transaction_id: str
    ) -> Claim:
        """Mark claim as paid after payout transaction."""
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError("Claim not found")
        
        claim.status = ClaimStatus.PAID
        claim.payout_transaction_id = transaction_id
        claim.payout_date = datetime.now()
        
        db.commit()
        db.refresh(claim)
        
        return claim
    
    @staticmethod
    def get_pending_claims(db: Session, limit: int = 100) -> List[Claim]:
        """Get pending claims for admin review."""
        return db.query(Claim).filter(
            Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW])
        ).order_by(
            Claim.fraud_score.desc(),  # High fraud scores first
            Claim.created_at.asc()
        ).limit(limit).all()

    @staticmethod
    def get_all_claims(
        db: Session,
        status: Optional[ClaimStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Claim]:
        """Get all claims for admin review with filtering."""
        query = db.query(Claim)
        
        if status:
            query = query.filter(Claim.status == status)
        
        if start_date:
            query = query.filter(Claim.created_at >= start_date)
            
        if end_date:
            query = query.filter(Claim.created_at <= end_date)
            
        return query.order_by(Claim.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_admin_stats(db: Session) -> dict:
        """Get claim counts by status for admin dashboard."""
        from sqlalchemy import func
        stats = db.query(Claim.status, func.count(Claim.id)).group_by(Claim.status).all()
        
        result = {
            "total": db.query(Claim).count(),
            "submitted": 0,
            "under_review": 0,
            "approved": 0,
            "rejected": 0,
            "paid": 0
        }
        
        for status_val, count in stats:
            if status_val in result:
                result[status_val] = count
                
        # Calculate pending as sum of submitted and under_review
        result["pending"] = result["submitted"] + result["under_review"]
        
        return result
