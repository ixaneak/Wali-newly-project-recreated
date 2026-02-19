"""
SAR (Suspicious Activity Reporting) Routes

Admin-only endpoints for CIMA AML compliance:
- Risk event monitoring
- SAR case management
- Compliance list screening
- TRACFIN report generation

All endpoints require admin authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
import logging

from app.core.database import get_db
from app.core.security_middleware_v2 import verify_admin
from app.services import sar_service, tracfin_service
from app.models.sar_report import SarReport
from app.models.risk_event import RiskEvent
from app.models.compliance_list import ComplianceListEntry

router = APIRouter(prefix="/api/v1/compliance/sar", tags=["sar-compliance"])
logger = logging.getLogger(__name__)


# ── Schemas ─────────────────────────────────────────────────────

class ScanTransactionRequest(BaseModel):
    """Manual risk scoring request."""
    user_id: str
    amount: int = Field(..., gt=0, description="Amount in XOF")
    phone: Optional[str] = None
    policy_id: Optional[str] = None
    claim_created_at: Optional[datetime] = None
    user_region: Optional[str] = None
    claim_location: Optional[str] = None
    payer_phone: Optional[str] = None
    policyholder_phone: Optional[str] = None


class EscalateRequest(BaseModel):
    """Escalate risk event to SAR."""
    analyst_notes: Optional[str] = None
    assigned_analyst: Optional[str] = None


class UpdateSarRequest(BaseModel):
    """Update SAR report."""
    status: Optional[str] = None
    review_notes: Optional[str] = None
    assigned_analyst: Optional[str] = None
    tracfin_reference: Optional[str] = None


class AddListEntryRequest(BaseModel):
    """Add entry to compliance list."""
    list_type: str = Field(..., description="whitelist, blacklist, pep, sanctions")
    identifier: str = Field(..., description="Phone, name, or device ID")
    identifier_type: str = Field(..., description="phone, name, device_id")
    reason: Optional[str] = None


class CloseSarRequest(BaseModel):
    """Close SAR report with resolution."""
    resolution: str = Field(..., description="Resolution: false_positive or confirmed_fraud")


class WhitelistRequest(BaseModel):
    """Quick-add to whitelist (reduces false positives)."""
    identifier: str
    identifier_type: str = Field(..., description="phone, name, device_id")
    reason: str


class ScreenRequest(BaseModel):
    """Screen identifier against compliance lists."""
    identifier: str


# ── Risk Events ─────────────────────────────────────────────────

@router.get("/risk-events")
def list_risk_events(
    severity: Optional[str] = None,
    policy_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """List risk events with optional filters."""
    query = db.query(RiskEvent)

    if severity:
        query = query.filter(RiskEvent.severity == severity)
    if policy_id:
        query = query.filter(RiskEvent.policy_id == policy_id)
    if start_date:
        query = query.filter(RiskEvent.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(RiskEvent.created_at <= datetime.combine(end_date, datetime.max.time()))

    total = query.count()
    events = query.order_by(RiskEvent.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "risk_events": [e.to_dict() for e in events],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/risk-events/{event_id}/escalate", status_code=status.HTTP_201_CREATED)
def escalate_risk_event(
    event_id: str,
    request: EscalateRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Escalate a risk event to a formal SAR report."""
    try:
        sar = sar_service.escalate_to_sar(
            db=db,
            risk_event_id=event_id,
            analyst_notes=request.analyst_notes,
            assigned_analyst=request.assigned_analyst or admin.get("email"),
        )
        return {
            "message": f"SAR report {sar.report_reference} created",
            "sar": sar.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── SAR Reports ─────────────────────────────────────────────────

@router.get("/reports")
def list_sar_reports(
    report_status: Optional[str] = Query(None, alias="status"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    risk_score_min: Optional[int] = Query(None, ge=0, le=100),
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """List SAR reports with optional filters."""
    query = db.query(SarReport)

    if report_status:
        query = query.filter(SarReport.status == report_status)
    if start_date:
        query = query.filter(SarReport.detection_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(SarReport.detection_date <= datetime.combine(end_date, datetime.max.time()))
    if risk_score_min is not None:
        query = query.filter(SarReport.risk_score >= risk_score_min)

    total = query.count()
    reports = query.order_by(SarReport.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "sar_reports": [r.to_dict() for r in reports],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/reports/{sar_id}")
def get_sar_report(
    sar_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Get full SAR report details with linked risk events and deadline info."""
    try:
        summary = tracfin_service.generate_tracfin_summary(db, sar_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/reports/{sar_id}")
def update_sar_report(
    sar_id: str,
    request: UpdateSarRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Update SAR report status, assignment, or notes."""
    try:
        sar = sar_service.update_sar_status(
            db=db,
            sar_id=sar_id,
            new_status=request.status,
            review_notes=request.review_notes,
            assigned_analyst=request.assigned_analyst,
            tracfin_reference=request.tracfin_reference,
        )
        return {"message": "SAR updated", "sar": sar.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reports/{sar_id}/submit-tracfin")
def submit_tracfin_report(
    sar_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Generate TRACFIN XML report and mark SAR as submitted."""
    try:
        xml_report = tracfin_service.generate_tracfin_xml(db, sar_id)

        # Transition to submitted
        sar = sar_service.update_sar_status(db, sar_id, new_status="submitted")

        return {
            "message": f"TRACFIN report generated for {sar.report_reference}",
            "xml": xml_report,
            "sar": sar.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reports/{sar_id}/close")
def close_sar_report(
    sar_id: str,
    request: CloseSarRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Close SAR with resolution (false_positive or confirmed_fraud)."""
    try:
        sar = sar_service.update_sar_status(
            db=db,
            sar_id=sar_id,
            new_status="closed",
            review_notes=f"Resolution: {request.resolution}",
        )
        return {"message": "SAR closed", "sar": sar.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Compliance Lists ────────────────────────────────────────────

@router.get("/lists")
def list_compliance_entries(
    list_type: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """List compliance list entries."""
    query = db.query(ComplianceListEntry)
    if list_type:
        query = query.filter(ComplianceListEntry.list_type == list_type)

    total = query.count()
    entries = query.order_by(ComplianceListEntry.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "entries": [e.to_dict() for e in entries],
        "total": total,
    }


@router.post("/lists", status_code=status.HTTP_201_CREATED)
def add_compliance_entry(
    request: AddListEntryRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Add an entry to a compliance list."""
    entry = ComplianceListEntry(
        list_type=request.list_type,
        identifier=request.identifier,
        identifier_type=request.identifier_type,
        reason=request.reason,
        added_by=admin.get("email") or admin.get("sub", "unknown"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {"message": "Entry added", "entry": entry.to_dict()}


@router.delete("/lists/{entry_id}")
def remove_compliance_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Remove a compliance list entry."""
    entry = db.query(ComplianceListEntry).filter(ComplianceListEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    db.delete(entry)
    db.commit()
    return {"message": "Entry removed", "id": entry_id}


@router.post("/screen")
def screen_identifier(
    request: ScreenRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Screen an identifier against all compliance lists."""
    result = sar_service.check_compliance_list(db, request.identifier)
    return result


@router.post("/whitelist", status_code=status.HTTP_201_CREATED)
def add_to_whitelist(
    request: WhitelistRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """Quick-add known-good customer to whitelist (reduces false positives)."""
    entry = ComplianceListEntry(
        list_type="whitelist",
        identifier=request.identifier,
        identifier_type=request.identifier_type,
        reason=request.reason,
        added_by=admin.get("email") or admin.get("sub", "unknown"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "added_to_whitelist", "entry": entry.to_dict()}


# ── Dashboard & Manual Scan ─────────────────────────────────────

@router.get("/dashboard")
def get_sar_dashboard(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """SAR compliance dashboard with overview statistics."""
    return sar_service.get_sar_dashboard(db)


@router.post("/scan-transaction")
def scan_transaction(
    request: ScanTransactionRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin),
):
    """
    Manually trigger risk scoring on a transaction.
    Creates a risk event if any rules fire.
    """
    result = sar_service.score_transaction(
        db=db,
        user_id=request.user_id,
        amount=request.amount,
        phone=request.phone,
        policy_id=request.policy_id,
        claim_created_at=request.claim_created_at,
        user_region=request.user_region,
        claim_location=request.claim_location,
        payer_phone=request.payer_phone,
        policyholder_phone=request.policyholder_phone,
    )

    # Auto-create risk event if any rules fired
    risk_event = None
    if result["rules_fired"] > 0:
        event = sar_service.create_risk_event(
            db=db,
            event_type="manual_scan",
            severity=result["severity"],
            risk_score=result["risk_score"],
            triggered_rules=result["triggered_rules"],
            user_id=request.user_id,
            user_phone=request.phone,
            policy_id=request.policy_id,
            raw_data={"amount": request.amount, "source": "manual_scan"},
        )
        risk_event = event.to_dict()

    return {
        "scoring_result": result,
        "risk_event": risk_event,
    }
