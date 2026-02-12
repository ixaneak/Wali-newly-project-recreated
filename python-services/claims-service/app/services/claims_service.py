"""
Incident Report Service (was: ClaimsService)

Manages incident reports filed by artisans and forwarded to partner insurers.
Wali does NOT process insurance claims — we collect incident data and
forward it to the partner insurer who handles decisions and payouts.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import logging

from app.models.claim import IncidentReport, IncidentStatus
from app.core.storage import minio_client
from app.validators.exif_validator import EXIFValidator
from app.validators.fraud_detector import FraudDetector

logger = logging.getLogger(__name__)


class IncidentReportService:
    """
    Service for managing incident reports.

    IMPORTANT: Wali does NOT make claim decisions or process payouts.
    We forward incident reports to the partner insurer who handles
    all claim adjudication and customer payments.
    """

    @staticmethod
    def submit_incident(
        db: Session,
        user_id: str,
        subscription_id: str,
        partner_id: str,
        incident_type: str,
        description: str,
        reported_amount: int,
        images: List[tuple[bytes, str]],
    ) -> IncidentReport:
        """
        Submit a new incident report for forwarding to partner insurer.

        Args:
            db: Database session
            user_id: Artisan's user ID
            subscription_id: Coverage subscription ID
            partner_id: Partner insurer (e.g. "NSIA")
            incident_type: Product ID from partner
            description: Incident description
            reported_amount: Amount reported by artisan
            images: Evidence photos

        Returns:
            Created IncidentReport
        """
        incident = IncidentReport(
            user_id=user_id,
            subscription_id=subscription_id,
            partner_id=partner_id,
            incident_type=incident_type,
            description=description,
            reported_amount=reported_amount,
            status=IncidentStatus.SUBMITTED,
        )

        db.add(incident)
        db.flush()  # Get ID

        incident_id = str(incident.id)
        image_urls = []
        image_hashes = []
        exif_data_list = []
        fraud_matches_all = []

        for image_data, filename in images:
            # Validate EXIF
            exif_result = EXIFValidator.validate_image(image_data)
            if not exif_result["valid"]:
                logger.warning(f"EXIF validation failed for incident {incident_id}")
                exif_data_list.append({"filename": filename, "valid": False, "errors": exif_result["errors"]})
            else:
                exif_data_list.append({"filename": filename, "valid": True, "data": exif_result["exif_data"]})

            # Fraud detection (tech service we provide)
            try:
                phash = FraudDetector.calculate_phash(image_data)
                image_hashes.append(phash)
                matches = FraudDetector.check_duplicate_images(db, phash, user_id, exclude_claim_id=incident_id)
                if matches:
                    fraud_matches_all.extend(matches)
                    logger.warning(f"Found {len(matches)} similar images for incident {incident_id}")
            except Exception as e:
                logger.error(f"Fraud detection failed: {e}")
                image_hashes.append(None)

            # Upload to MinIO
            file_extension = "." + filename.split(".")[-1] if "." in filename else ".jpg"
            try:
                object_name = minio_client.upload_image(image_data, incident_id, file_extension)
                presigned_url = minio_client.get_presigned_url(object_name)
                image_urls.append(presigned_url)
            except Exception as e:
                logger.error(f"Image upload failed: {e}")
                raise ValueError(f"Failed to upload image: {str(e)}")

        # Fraud analysis (technology service Wali provides)
        fraud_analysis = FraudDetector.detect_fraud_patterns(fraud_matches_all)

        fraud_score = 0
        if fraud_analysis["fraud_detected"]:
            if fraud_analysis["risk_level"] == "critical":
                fraud_score = 95
            elif fraud_analysis["risk_level"] == "high":
                fraud_score = 75
            elif fraud_analysis["risk_level"] == "medium":
                fraud_score = 50

        incident.image_urls = image_urls
        incident.image_hashes = [h for h in image_hashes if h is not None]
        incident.exif_data = {"images": exif_data_list}
        incident.fraud_score = fraud_score
        incident.fraud_flags = fraud_analysis

        if fraud_analysis["fraud_detected"]:
            incident.status = IncidentStatus.UNDER_REVIEW
            logger.warning(f"Incident {incident_id} flagged for review: {fraud_analysis['patterns']}")

        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def get_incident(db: Session, incident_id: str) -> Optional[IncidentReport]:
        """Get a single incident report by ID."""
        return db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()

    @staticmethod
    def get_user_incidents(
        db: Session,
        user_id: str,
        status: Optional[IncidentStatus] = None,
    ) -> List[IncidentReport]:
        """Get all incident reports for an artisan."""
        query = db.query(IncidentReport).filter(IncidentReport.user_id == user_id)
        if status:
            query = query.filter(IncidentReport.status == status)
        return query.order_by(IncidentReport.created_at.desc()).all()

    @staticmethod
    def review_incident(
        db: Session,
        incident_id: str,
        reviewer_id: str,
        forward_to_partner: bool,
        partner_approved_amount: Optional[int] = None,
        review_notes: Optional[str] = None,
    ) -> IncidentReport:
        """
        Review incident report before forwarding to partner insurer.

        If forward_to_partner=True, marks as ready for partner.
        The partner makes the final claim decision.
        """
        incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
        if not incident:
            raise ValueError("Incident report not found")

        incident.reviewer_id = reviewer_id
        incident.review_notes = review_notes
        incident.reviewed_at = datetime.now()

        if forward_to_partner:
            incident.status = IncidentStatus.FORWARDED_TO_PARTNER
            incident.forwarded_to_partner_at = datetime.now()
            if partner_approved_amount:
                incident.partner_approved_amount = partner_approved_amount
        else:
            incident.status = IncidentStatus.PARTNER_REJECTED  # Wali pre-screen rejection

        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def forward_to_partner(
        db: Session,
        incident_id: str,
        partner_reference: str,
    ) -> IncidentReport:
        """
        Record that incident was forwarded to partner insurer.

        The partner_reference is the partner's internal case number.
        From here, the partner manages the claim process.
        """
        incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
        if not incident:
            raise ValueError("Incident report not found")

        incident.status = IncidentStatus.FORWARDED_TO_PARTNER
        incident.partner_reference = partner_reference
        incident.forwarded_to_partner_at = datetime.now()

        db.commit()
        db.refresh(incident)

        logger.info(
            "Incident %s forwarded to partner %s (ref: %s). Wali role: technology_provider",
            incident.incident_number, incident.partner_id, partner_reference,
        )
        return incident

    @staticmethod
    def get_pending_incidents(db: Session, limit: int = 100) -> List[IncidentReport]:
        """Get pending incident reports for review."""
        return db.query(IncidentReport).filter(
            IncidentReport.status.in_([IncidentStatus.SUBMITTED, IncidentStatus.UNDER_REVIEW])
        ).order_by(
            IncidentReport.fraud_score.desc(),
            IncidentReport.created_at.asc(),
        ).limit(limit).all()

    @staticmethod
    def get_all_incidents(
        db: Session,
        partner_id: str = None,
        status: Optional[IncidentStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[IncidentReport]:
        """Get all incident reports with filtering."""
        query = db.query(IncidentReport)
        if partner_id:
            query = query.filter(IncidentReport.partner_id == partner_id)
        if status:
            query = query.filter(IncidentReport.status == status)
        if start_date:
            query = query.filter(IncidentReport.created_at >= start_date)
        if end_date:
            query = query.filter(IncidentReport.created_at <= end_date)
        return query.order_by(IncidentReport.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_admin_stats(db: Session, partner_id: str = None) -> dict:
        """Get incident report statistics for admin dashboard."""
        from sqlalchemy import func

        query = db.query(IncidentReport)
        if partner_id:
            query = query.filter(IncidentReport.partner_id == partner_id)

        stats = query.with_entities(
            IncidentReport.status, func.count(IncidentReport.id)
        ).group_by(IncidentReport.status).all()

        result = {
            "total": query.count(),
            "submitted": 0,
            "under_review": 0,
            "forwarded_to_partner": 0,
            "partner_approved": 0,
            "partner_rejected": 0,
            "partner_paid": 0,
            "wali_role": "technology_provider",
        }

        for status_val, count in stats:
            key = status_val.value if hasattr(status_val, "value") else str(status_val)
            if key in result:
                result[key] = count

        result["pending"] = result["submitted"] + result["under_review"]
        return result


# Backward-compatible alias
ClaimsService = IncidentReportService
