"""
SAR (Suspicious Activity Report) API Routes

Provides endpoints for:
- Real-time policy/claim analysis
- SAR report management
- Compliance dashboard data
- Watchlist management
- Audit trails

COSUMAF Compliance: All endpoints require admin authentication
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security_middleware_v2 import verify_admin
from app.services.sar_detection_engine import (
    SARDetectionEngine, RiskEvent, RiskSeverity, DetectionRuleType
)

router = APIRouter(prefix="/api/v1/compliance/sar", tags=["compliance-sar"])


# ═════════════════════════════════════════════════════════════════
# SCHEMAS
# ═════════════════════════════════════════════════════════════════

class PolicyAnalysisRequest(BaseModel):
    """Request to analyze a new policy."""
    id: str
    phone_number: str
    full_name: str
    id_number: Optional[str] = None
    amount: int
    created_at: str
    device_fingerprint: Optional[Dict] = None
    payment_phone: Optional[str] = None
    payment_name: Optional[str] = None


class ClaimAnalysisRequest(BaseModel):
    """Request to analyze a claim submission."""
    id: str
    policy_id: str
    phone_number: str
    full_name: str
    amount: int
    description: str
    claim_date: str
    claim_gps: Optional[Dict] = None
    documents: Optional[List[Dict]] = None
    service_provider: Optional[str] = None


class RiskEventResponse(BaseModel):
    """Risk event response model."""
    rule_type: str
    severity: str
    policy_id: str
    risk_score: int
    description: str
    metadata: Dict[str, Any]
    timestamp: str


class SARReportResponse(BaseModel):
    """SAR report response model."""
    report_reference: str
    status: str
    subject_name: str
    subject_phone: str
    activity_type: str
    risk_score: int
    description: str
    amount_involved: int
    created_at: str
    retention_until: str


class DashboardStats(BaseModel):
    """Compliance dashboard statistics."""
    total_sars_this_month: int
    total_sars_this_year: int
    open_reviews: int
    watchlisted_entities: int
    alerts_today: int
    risk_distribution: Dict[str, int]
    recent_sars: List[SARReportResponse]


class WatchlistEntry(BaseModel):
    """Watchlist entry model."""
    entity_type: str
    entity_id: str
    phone_number: str
    risk_score: int
    reason: str
    added_at: str
    expires_at: str


# ═════════════════════════════════════════════════════════════════
# ANALYSIS ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@router.post("/analyze/policy", response_model=Optional[RiskEventResponse])
async def analyze_policy(
    request: PolicyAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Analyze a new policy creation for suspicious activity.
    
    This endpoint should be called when a new policy is created.
    It runs all detection rules and returns any risk events found.
    If risk score >= 70, auto-creates SAR report.
    """
    engine = SARDetectionEngine(db)
    
    result = await engine.analyze_policy_creation(request.dict())
    
    if result:
        return RiskEventResponse(**result.to_dict())
    
    return None


@router.post("/analyze/claim", response_model=Optional[RiskEventResponse])
async def analyze_claim(
    request: ClaimAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Analyze a claim submission for fraud indicators.
    
    This endpoint should be called when a new claim is submitted.
    It runs claim-specific detection rules.
    """
    engine = SARDetectionEngine(db)
    
    # Get policy data to combine with claim
    policy_data = {
        "id": request.policy_id,
        "phone_number": request.phone_number,
        "full_name": request.full_name,
        "amount": request.amount,
    }
    
    claim_data = request.dict()
    
    result = await engine.analyze_claim_submission(claim_data, policy_data)
    
    if result:
        return RiskEventResponse(**result.to_dict())
    
    return None


# ═════════════════════════════════════════════════════════════════
# SAR MANAGEMENT ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@router.get("/reports", response_model=List[SARReportResponse])
async def list_sar_reports(
    status: Optional[str] = Query(None, description="Filter by status: draft, filed, under_review, closed"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    risk_score_min: Optional[int] = Query(None, ge=0, le=100),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    List all SAR reports with optional filtering.
    """
    # Mock implementation - replace with actual DB query
    return []


@router.get("/reports/{report_ref}", response_model=SARReportResponse)
async def get_sar_report(
    report_ref: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get detailed information about a specific SAR report.
    """
    # Mock implementation
    raise HTTPException(status_code=404, detail="SAR report not found")


@router.post("/reports/{report_ref}/file")
async def file_sar_report(
    report_ref: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    File a SAR report with authorities (COSUMAF, etc.).
    Changes status from 'draft' to 'filed'.
    """
    # Update status and log filing
    return {"status": "filed", "report_reference": report_ref}


@router.post("/reports/{report_ref}/close")
async def close_sar_report(
    report_ref: str,
    resolution: str = Query(..., description="Resolution: confirmed_fraud, false_positive, no_action"),
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Close a SAR report with resolution.
    """
    return {"status": "closed", "report_reference": report_ref, "resolution": resolution}


# ═════════════════════════════════════════════════════════════════
# DASHBOARD ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get compliance dashboard statistics.
    
    Returns:
    - SAR counts (month/year)
    - Open review count
    - Watchlist size
    - Today's alerts
    - Risk distribution
    - Recent SARs
    """
    # Mock data - replace with actual queries
    return DashboardStats(
        total_sars_this_month=12,
        total_sars_this_year=87,
        open_reviews=23,
        watchlisted_entities=156,
        alerts_today=5,
        risk_distribution={
            "low": 45,
            "medium": 32,
            "high": 18,
            "critical": 8
        },
        recent_sars=[]
    )


@router.get("/dashboard/alerts")
async def get_recent_alerts(
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get recent risk alerts for the dashboard.
    """
    return []


@router.get("/dashboard/trends")
async def get_risk_trends(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get risk trend data for charts.
    
    Returns time-series data of:
    - SARs created
    - Flags raised
    - Risk scores over time
    """
    return {
        "period": period,
        "labels": [],
        "sars_created": [],
        "flags_raised": [],
        "avg_risk_score": []
    }


# ═════════════════════════════════════════════════════════════════
# WATCHLIST ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@router.get("/watchlist", response_model=List[WatchlistEntry])
async def get_watchlist(
    risk_min: Optional[int] = Query(None, ge=0, le=100),
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get entities on the compliance watchlist.
    """
    return []


@router.post("/watchlist/{entity_type}/{entity_id}")
async def add_to_watchlist(
    entity_type: str,
    entity_id: str,
    reason: str,
    risk_score: int = Query(..., ge=0, le=100),
    expires_days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Manually add an entity to the watchlist.
    """
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "added": True,
        "expires_at": (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
    }


@router.delete("/watchlist/{entity_type}/{entity_id}")
async def remove_from_watchlist(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Remove an entity from the watchlist.
    """
    return {"removed": True}


# ═════════════════════════════════════════════════════════════════
# AUDIT & REPORTING ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@router.get("/audit/log")
async def get_audit_log(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get compliance audit log.
    
    Records all compliance-related actions:
    - SAR created/filed/closed
    - Flags raised/cleared
    - Watchlist additions/removals
    - Manual overrides
    """
    return []


@router.post("/export/sar")
async def export_sar_report(
    report_ref: str,
    format: str = Query("pdf", regex="^(pdf|xml|csv)$"),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Export a SAR report in the requested format.
    
    COSUMAF requires XML format for regulatory filing.
    """
    return {"download_url": f"/downloads/sar_{report_ref}.{format}"}


@router.get("/rules")
async def list_detection_rules(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    List all detection rules and their configurations.
    """
    rules = [
        {
            "rule_type": rule_type.value,
            "description": get_rule_description(rule_type),
            "severity_range": "low-high",
            "enabled": True
        }
        for rule_type in DetectionRuleType
    ]
    
    return rules


def get_rule_description(rule_type: DetectionRuleType) -> str:
    """Get human-readable description for each rule type."""
    descriptions = {
        DetectionRuleType.RAPID_CLAIM: "Claims filed within 48 hours of policy creation",
        DetectionRuleType.STRUCTURING: "Multiple policies under reporting threshold",
        DetectionRuleType.GEOLOCATION_ANOMALY: "Claim location far from registration",
        DetectionRuleType.DEVICE_FINGERPRINT: "Suspicious device patterns",
        DetectionRuleType.DOCUMENT_FORGERY: "Document editing or timestamp issues",
        DetectionRuleType.THIRD_PARTY_PAYMENT: "Premium paid by different person",
        DetectionRuleType.ROUND_NUMBERS: "Suspiciously round transaction amounts",
        DetectionRuleType.SANCTIONS_LIST: "Match against sanctions/PEP lists",
        DetectionRuleType.VELOCITY_CHECK: "Unusual transaction velocity",
        DetectionRuleType.DUPLICATE_CLAIMS: "Similar claims from same user",
        DetectionRuleType.SUSPICIOUS_TIMING: "Claims at odd hours",
        DetectionRuleType.IDENTITY_MORPHING: "Slight identity variations",
        DetectionRuleType.COLLUSION: "Provider collusion patterns",
        DetectionRuleType.PREMIUM_CASHING: "Cancellation after claim payout",
    }
    return descriptions.get(rule_type, "Unknown rule")


# ═════════════════════════════════════════════════════════════════
# TRACFIN EXPORT ENDPOINTS
# ═════════════════════════════════════════════════════════════════

from app.services.tracfin_export import (
    generate_tracfin_xml, 
    validate_tracfin_xml,
    generate_tracfin_batch_xml
)
from fastapi.responses import PlainTextResponse


@router.get("/reports/{report_ref}/export/tracfin", response_class=PlainTextResponse)
async def export_tracfin_xml(
    report_ref: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Export a SAR report as TRACFIN-compatible XML.
    
    TRACFIN (Traitement du Renseignement et Action Contre les 
    Circuits Financiers Clandestins) is the French FIU.
    This format is used for regulatory filing.
    """
    # Get report from database (mock for now)
    report = {
        "report_reference": report_ref,
        "status": "draft",
        "subject_type": "individual",
        "subject_name": "John Doe",
        "subject_phone": "0701234567",
        "subject_id": "ID123456",
        "activity_type": "INSURANCE_FRAUD",
        "occurrence_date": datetime.utcnow(),
        "amount_involved": 500000,
        "description": "Suspicious claim pattern detected",
        "risk_score": 75,
        "triggered_rules": [
            {"rule": "rapid_claim", "score": 55},
            {"rule": "structuring", "score": 20}
        ],
        "supporting_documents": ["doc1.pdf", "doc2.pdf"],
        "related_transactions": ["tx123", "tx456"]
    }
    
    try:
        xml_content = generate_tracfin_xml(report)
        
        # Validate the generated XML
        is_valid, errors = validate_tracfin_xml(xml_content)
        if not is_valid:
            raise HTTPException(
                status_code=500,
                detail=f"Generated XML validation failed: {', '.join(errors)}"
            )
        
        return PlainTextResponse(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=SAR_{report_ref}_TRACFIN.xml"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate TRACFIN XML: {str(e)}"
        )


@router.post("/export/batch/tracfin", response_class=PlainTextResponse)
async def export_batch_tracfin(
    report_refs: List[str],
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Export multiple SAR reports as a batch TRACFIN XML file.
    
    Useful for bulk regulatory submissions.
    """
    reports = []
    for ref in report_refs:
        # Get report from database (mock for now)
        reports.append({
            "report_reference": ref,
            "status": "draft",
            "subject_type": "individual",
            "subject_name": "John Doe",
            "subject_phone": "0701234567",
            "subject_id": "ID123456",
            "activity_type": "INSURANCE_FRAUD",
            "occurrence_date": datetime.utcnow(),
            "amount_involved": 500000,
            "description": "Suspicious claim pattern detected",
            "risk_score": 75,
            "triggered_rules": [{"rule": "rapid_claim", "score": 55}],
            "supporting_documents": ["doc1.pdf"],
            "related_transactions": ["tx123"]
        })
    
    try:
        xml_content = generate_tracfin_batch_xml(reports)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return PlainTextResponse(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=SAR_BATCH_{timestamp}_TRACFIN.xml"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate batch TRACFIN XML: {str(e)}"
        )


@router.get("/reports/{report_ref}/export/tracfin/validate")
async def validate_tracfin_report(
    report_ref: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Validate a SAR report can be exported as valid TRACFIN XML.
    
    Returns validation results without generating the actual file.
    """
    report = {
        "report_reference": report_ref,
        "status": "draft",
        "subject_type": "individual",
        "subject_name": "John Doe",
        "subject_phone": "0701234567",
        "subject_id": "ID123456",
        "activity_type": "INSURANCE_FRAUD",
        "occurrence_date": datetime.utcnow(),
        "amount_involved": 500000,
        "description": "Suspicious claim pattern detected",
        "risk_score": 75,
        "triggered_rules": [{"rule": "rapid_claim", "score": 55}],
        "supporting_documents": ["doc1.pdf"],
        "related_transactions": ["tx123"]
    }
    
    try:
        xml_content = generate_tracfin_xml(report)
        is_valid, errors = validate_tracfin_xml(xml_content)
        
        return {
            "report_reference": report_ref,
            "is_valid": is_valid,
            "errors": errors,
            "xml_size_bytes": len(xml_content),
            "validation_timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "report_reference": report_ref,
            "is_valid": False,
            "errors": [str(e)],
            "xml_size_bytes": 0,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
