"""
SAR Detection Background Tasks

Async processing of compliance checks to avoid blocking API responses.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from infrastructure.celery.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def analyze_claim_for_sar(self, claim_id: str, claim_data: Dict[str, Any]):
    """
    Analyze a claim submission for suspicious activity.
    
    This runs asynchronously after claim submission to not block
    the user's request.
    
    Args:
        claim_id: The claim/incident ID
        claim_data: Dictionary containing claim details
    """
    try:
        logger.info(f"Starting SAR analysis for claim {claim_id}")
        
        # Import here to avoid circular dependencies
        from app.services.sar_detection_engine import SARDetectionEngine
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            engine = SARDetectionEngine(db)
            
            # Run analysis
            risk_event = engine.analyze_claim_submission(claim_data, {})
            
            if risk_event:
                logger.warning(
                    f"SAR risk detected for claim {claim_id}: "
                    f"{risk_event.rule_type} (Score: {risk_event.risk_score})"
                )
                
                # Update claim with fraud score
                from app.models.claim import Claim
                claim = db.query(Claim).filter(Claim.id == claim_id).first()
                if claim:
                    claim.fraud_score = risk_event.risk_score
                    claim.fraud_flags = {
                        'sar_detection': risk_event.to_dict(),
                        'analyzed_at': datetime.utcnow().isoformat(),
                    }
                    db.commit()
                
                return {
                    'status': 'risk_detected',
                    'claim_id': claim_id,
                    'risk_score': risk_event.risk_score,
                    'rule_type': risk_event.rule_type,
                }
            else:
                logger.info(f"No SAR risk detected for claim {claim_id}")
                return {
                    'status': 'clean',
                    'claim_id': claim_id,
                }
                
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"SAR analysis failed for claim {claim_id}: {exc}")
        # Retry with exponential backoff
        retry_count = self.request.retries
        countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, max_retries=3)
def analyze_policy_for_sar(self, policy_id: str, policy_data: Dict[str, Any]):
    """
    Analyze a new policy enrollment for suspicious patterns.
    
    Detects:
    - Structuring (multiple small policies)
    - Rapid enrollment patterns
    - Sanctions list matches
    """
    try:
        logger.info(f"Starting SAR analysis for policy {policy_id}")
        
        from app.services.sar_detection_engine import SARDetectionEngine
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            engine = SARDetectionEngine(db)
            
            risk_event = engine.analyze_policy_creation(policy_data)
            
            if risk_event:
                logger.warning(
                    f"SAR risk detected for policy {policy_id}: "
                    f"{risk_event.rule_type} (Score: {risk_event.risk_score})"
                )
                return {
                    'status': 'risk_detected',
                    'policy_id': policy_id,
                    'risk_score': risk_event.risk_score,
                }
            else:
                return {
                    'status': 'clean',
                    'policy_id': policy_id,
                }
                
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"SAR analysis failed for policy {policy_id}: {exc}")
        retry_count = self.request.retries
        countdown = 60 * (2 ** retry_count)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True)
def generate_sar_report(self, sar_report_id: str):
    """
    Generate a formal SAR report document.
    
    Creates TRACFIN-compatible XML and PDF for regulatory filing.
    """
    try:
        logger.info(f"Generating SAR report {sar_report_id}")
        
        from app.services.tracfin_export import generate_tracfin_xml
        from app.models.sar_report import SarReport
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            report = db.query(SarReport).filter(SarReport.id == sar_report_id).first()
            if not report:
                return {'status': 'error', 'message': 'Report not found'}
            
            # Generate XML
            xml_content = generate_tracfin_xml(report.to_dict())
            
            # Store document reference (in production, upload to S3)
            report.supporting_documents = report.supporting_documents or []
            report.supporting_documents.append({
                'type': 'tracfin_xml',
                'generated_at': datetime.utcnow().isoformat(),
                'size_bytes': len(xml_content),
            })
            db.commit()
            
            return {
                'status': 'success',
                'sar_report_id': sar_report_id,
                'xml_size': len(xml_content),
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"SAR report generation failed: {exc}")
        return {'status': 'error', 'message': str(exc)}


@celery_app.task
def submit_sar_to_tracfin(sar_report_id: str):
    """
    Submit a SAR report to TRACFIN.
    
    This would integrate with TRACFIN's API in production.
    For now, simulates the submission process.
    """
    logger.info(f"Submitting SAR {sar_report_id} to TRACFIN")
    
    # TODO: Implement actual TRACFIN API integration
    # This would use their secure file upload endpoint
    
    return {
        'status': 'submitted',
        'sar_report_id': sar_report_id,
        'tracfin_reference': f'TRACFIN-{datetime.utcnow().strftime("%Y%m%d")}-{sar_report_id[:8]}',
        'submitted_at': datetime.utcnow().isoformat(),
    }
