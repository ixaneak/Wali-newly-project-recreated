"""
SAR Service — Risk Scoring Engine & Case Management

Implements 7 detection rules per CIMA AML requirements for micro-insurance:
1. Structuring (multiple policies below threshold)
2. Rapid claims (claim within 48h of policy purchase)
3. Round numbers (suspicious amounts in exact multiples)
4. High-velocity (multiple accounts from same phone prefix)
5. Threshold breach (transactions > 500,000 XOF)
6. Identity inconsistency (region mismatch)
7. Third-party payments (payer ≠ policyholder)
"""
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from app.models.sar_report import SarReport, SarStatus
from app.models.risk_event import RiskEvent, RiskSeverity
from app.models.compliance_list import ComplianceListEntry
from app.models.policy import CoverageSubscription
from app.models.claim import Claim

logger = logging.getLogger(__name__)

# ── Thresholds ──────────────────────────────────────────────────
THRESHOLD_AMOUNT_XOF = 500_000       # CIMA reporting threshold (~$800)
STRUCTURING_WINDOW_DAYS = 30         # Window for structuring detection
STRUCTURING_POLICY_COUNT = 3         # Min policies to flag
RAPID_CLAIM_HOURS = 48               # Claim within N hours = suspicious
HIGH_VELOCITY_COUNT = 3              # N accounts from same prefix in 24h
ROUND_NUMBER_MIN_AMOUNT = 50_000     # Only flag round numbers above this


# ── Risk Detection Rules ────────────────────────────────────────

def _rule_structuring(db: Session, user_id: str) -> tuple[bool, int, dict]:
    """
    Rule 1: Detect structuring — multiple small policies just under threshold.
    Returns (fired, score, context).
    """
    window_start = datetime.utcnow() - timedelta(days=STRUCTURING_WINDOW_DAYS)
    policies = (
        db.query(CoverageSubscription)
        .filter(
            CoverageSubscription.user_id == user_id,
            CoverageSubscription.created_at >= window_start,
        )
        .all()
    )
    count = len(policies)
    total_amount = sum(p.partner_quoted_amount for p in policies if p.partner_quoted_amount)

    if count >= STRUCTURING_POLICY_COUNT and total_amount > THRESHOLD_AMOUNT_XOF:
        # Multiple policies that individually are small but collectively exceed threshold
        return True, 40, {
            "rule": "structuring",
            "policy_count": count,
            "total_amount": total_amount,
            "window_days": STRUCTURING_WINDOW_DAYS,
        }
    return False, 0, {}


def _rule_rapid_claim(db: Session, policy_id: str, claim_created_at: datetime) -> tuple[bool, int, dict]:
    """
    Rule 2: Detect rapid claims — claim filed within 48 hours of policy start.
    """
    policy = db.query(CoverageSubscription).filter(CoverageSubscription.id == policy_id).first()
    if not policy or not policy.start_date:
        return False, 0, {}

    hours_diff = (claim_created_at - policy.start_date).total_seconds() / 3600
    if hours_diff < RAPID_CLAIM_HOURS:
        return True, 55, {
            "rule": "rapid_claim",
            "hours_since_policy_start": round(hours_diff, 1),
            "threshold_hours": RAPID_CLAIM_HOURS,
            "policy_id": policy_id,
        }
    return False, 0, {}


def _rule_round_number(amount: int) -> tuple[bool, int, dict]:
    """
    Rule 3: Detect suspicious round numbers (amounts in exact multiples of 1000 above threshold).
    """
    if amount >= ROUND_NUMBER_MIN_AMOUNT and amount % 1000 == 0:
        return True, 15, {
            "rule": "round_number",
            "amount": amount,
            "note": "Amount is an exact multiple of 1000 XOF",
        }
    return False, 0, {}


def _rule_high_velocity(db: Session, phone: str) -> tuple[bool, int, dict]:
    """
    Rule 4: Detect high-velocity — multiple accounts created from same phone prefix in 24h.
    """
    if not phone or len(phone) < 6:
        return False, 0, {}

    prefix = phone[:6]  # Country code + first digits
    window_start = datetime.utcnow() - timedelta(hours=24)

    from app.models.policy import User
    count = (
        db.query(User)
        .filter(
            User.phone.like(f"{prefix}%"),
            User.created_at >= window_start,
        )
        .count()
    )

    if count >= HIGH_VELOCITY_COUNT:
        return True, 50, {
            "rule": "high_velocity",
            "phone_prefix": prefix,
            "accounts_in_24h": count,
            "threshold": HIGH_VELOCITY_COUNT,
        }
    return False, 0, {}


def _rule_threshold_breach(amount: int) -> tuple[bool, int, dict]:
    """
    Rule 5: Flag any single transaction exceeding 500,000 XOF.
    """
    if amount > THRESHOLD_AMOUNT_XOF:
        return True, 60, {
            "rule": "threshold_breach",
            "amount": amount,
            "threshold": THRESHOLD_AMOUNT_XOF,
        }
    return False, 0, {}


def _rule_identity_inconsistency(user_region: Optional[str], claim_location: Optional[str]) -> tuple[bool, int, dict]:
    """
    Rule 6: Region mismatch between policyholder and claim location.
    """
    if not user_region or not claim_location:
        return False, 0, {}

    if user_region.lower().strip() != claim_location.lower().strip():
        return True, 30, {
            "rule": "identity_inconsistency",
            "user_region": user_region,
            "claim_location": claim_location,
        }
    return False, 0, {}


def _rule_third_party_payment(payer_phone: Optional[str], policyholder_phone: Optional[str]) -> tuple[bool, int, dict]:
    """
    Rule 7: Payment made by a different person than the policyholder.
    """
    if not payer_phone or not policyholder_phone:
        return False, 0, {}

    if payer_phone != policyholder_phone:
        return True, 35, {
            "rule": "third_party_payment",
            "payer_phone": payer_phone[-4:],  # Only last 4 digits for privacy
            "policyholder_phone": policyholder_phone[-4:],
        }
    return False, 0, {}


# ── Core Service Methods ────────────────────────────────────────

def score_transaction(
    db: Session,
    user_id: str,
    amount: int,
    phone: Optional[str] = None,
    policy_id: Optional[str] = None,
    claim_created_at: Optional[datetime] = None,
    user_region: Optional[str] = None,
    claim_location: Optional[str] = None,
    payer_phone: Optional[str] = None,
    policyholder_phone: Optional[str] = None,
) -> dict:
    """
    Run all 7 risk rules against a transaction and return the aggregate score.
    Returns a dict with total score, severity, and all triggered rules.
    """
    triggered_rules = []
    total_score = 0

    # Rule 1: Structuring
    fired, score, ctx = _rule_structuring(db, user_id)
    if fired:
        triggered_rules.append(ctx)
        total_score += score

    # Rule 2: Rapid claim
    if policy_id and claim_created_at:
        fired, score, ctx = _rule_rapid_claim(db, policy_id, claim_created_at)
        if fired:
            triggered_rules.append(ctx)
            total_score += score

    # Rule 3: Round number
    fired, score, ctx = _rule_round_number(amount)
    if fired:
        triggered_rules.append(ctx)
        total_score += score

    # Rule 4: High velocity
    if phone:
        fired, score, ctx = _rule_high_velocity(db, phone)
        if fired:
            triggered_rules.append(ctx)
            total_score += score

    # Rule 5: Threshold breach
    fired, score, ctx = _rule_threshold_breach(amount)
    if fired:
        triggered_rules.append(ctx)
        total_score += score

    # Rule 6: Identity inconsistency
    fired, score, ctx = _rule_identity_inconsistency(user_region, claim_location)
    if fired:
        triggered_rules.append(ctx)
        total_score += score

    # Rule 7: Third-party payment
    fired, score, ctx = _rule_third_party_payment(payer_phone, policyholder_phone)
    if fired:
        triggered_rules.append(ctx)
        total_score += score

    # Cap at 100
    total_score = min(total_score, 100)

    # Determine severity
    if total_score >= 70:
        severity = RiskSeverity.CRITICAL.value
    elif total_score >= 50:
        severity = RiskSeverity.HIGH.value
    elif total_score >= 25:
        severity = RiskSeverity.MEDIUM.value
    else:
        severity = RiskSeverity.LOW.value

    return {
        "risk_score": total_score,
        "severity": severity,
        "triggered_rules": triggered_rules,
        "rules_checked": 7,
        "rules_fired": len(triggered_rules),
    }


def create_risk_event(
    db: Session,
    event_type: str,
    severity: str,
    risk_score: int,
    triggered_rules: list,
    user_id: Optional[str] = None,
    user_phone: Optional[str] = None,
    policy_id: Optional[str] = None,
    claim_id: Optional[str] = None,
    raw_data: Optional[dict] = None,
) -> RiskEvent:
    """Create and persist a risk event in the detection log."""
    event = RiskEvent(
        id=str(uuid.uuid4()),
        event_type=event_type,
        severity=severity,
        risk_score=risk_score,
        triggered_rules=triggered_rules,
        user_id=user_id,
        user_phone=user_phone,
        policy_id=policy_id,
        claim_id=claim_id,
        raw_data=raw_data or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    logger.info(f"Risk event created: {event.id} type={event_type} severity={severity} score={risk_score}")
    return event


def escalate_to_sar(
    db: Session,
    risk_event_id: str,
    analyst_notes: Optional[str] = None,
    assigned_analyst: Optional[str] = None,
) -> SarReport:
    """Escalate a risk event to a formal SAR report."""
    risk_event = db.query(RiskEvent).filter(RiskEvent.id == risk_event_id).first()
    if not risk_event:
        raise ValueError(f"Risk event {risk_event_id} not found")

    if risk_event.sar_report_id:
        raise ValueError(f"Risk event {risk_event_id} already escalated to SAR {risk_event.sar_report_id}")

    # Determine activity type from first triggered rule
    rules = risk_event.triggered_rules or []
    activity_type = rules[0].get("rule", "unknown") if rules else risk_event.event_type

    sar = SarReport(
        id=str(uuid.uuid4()),
        report_reference=f"SAR-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}",
        status=SarStatus.DRAFT.value,
        subject_type="policyholder",
        subject_id=risk_event.user_id or risk_event.user_phone or "unknown",
        subject_phone=risk_event.user_phone,
        activity_type=activity_type,
        occurrence_date=risk_event.created_at or datetime.utcnow(),
        description=f"Automated escalation from risk event {risk_event.id}. "
                    f"Rules triggered: {[r.get('rule') for r in rules]}. "
                    f"Score: {risk_event.risk_score}/100.",
        amount_involved=risk_event.raw_data.get("amount") if risk_event.raw_data else None,
        risk_score=risk_event.risk_score,
        assigned_analyst=assigned_analyst,
        review_notes=analyst_notes,
        related_transactions=[risk_event.policy_id, risk_event.claim_id],
    )
    db.add(sar)

    # Link risk event to SAR
    risk_event.sar_report_id = sar.id
    db.commit()
    db.refresh(sar)

    logger.info(f"SAR created: {sar.report_reference} from risk event {risk_event_id}")
    return sar


def update_sar_status(
    db: Session,
    sar_id: str,
    new_status: str,
    review_notes: Optional[str] = None,
    assigned_analyst: Optional[str] = None,
    tracfin_reference: Optional[str] = None,
) -> SarReport:
    """Update SAR report status and metadata."""
    sar = db.query(SarReport).filter(SarReport.id == sar_id).first()
    if not sar:
        raise ValueError(f"SAR report {sar_id} not found")

    # Validate transition
    valid_transitions = {
        "draft": ["submitted", "closed"],
        "submitted": ["under_review", "closed"],
        "under_review": ["closed"],
    }
    current = sar.status
    allowed = valid_transitions.get(current, [])
    if new_status not in allowed:
        raise ValueError(f"Cannot transition SAR from '{current}' to '{new_status}'. Allowed: {allowed}")

    sar.status = new_status
    if review_notes:
        sar.review_notes = review_notes
    if assigned_analyst:
        sar.assigned_analyst = assigned_analyst
    if tracfin_reference:
        sar.tracfin_reference = tracfin_reference
    if new_status == "submitted":
        sar.submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(sar)

    logger.info(f"SAR {sar.report_reference} transitioned to '{new_status}'")
    return sar


def check_compliance_list(db: Session, identifier: str) -> dict:
    """Screen an identifier against all compliance lists."""
    now = datetime.utcnow()
    matches = (
        db.query(ComplianceListEntry)
        .filter(
            ComplianceListEntry.identifier == identifier,
        )
        .all()
    )

    # Filter out expired entries
    active = [
        m for m in matches
        if m.expires_at is None or m.expires_at > now
    ]

    results = {
        "identifier": identifier,
        "match_count": len(active),
        "is_blacklisted": any(m.list_type == "blacklist" for m in active),
        "is_pep": any(m.list_type == "pep" for m in active),
        "is_sanctioned": any(m.list_type == "sanctions" for m in active),
        "is_whitelisted": any(m.list_type == "whitelist" for m in active),
        "matches": [m.to_dict() for m in active],
    }
    return results


def get_sar_dashboard(db: Session) -> dict:
    """Get overview statistics for SAR dashboard."""
    total_sars = db.query(SarReport).count()
    draft = db.query(SarReport).filter(SarReport.status == "draft").count()
    submitted = db.query(SarReport).filter(SarReport.status == "submitted").count()
    under_review = db.query(SarReport).filter(SarReport.status == "under_review").count()
    closed = db.query(SarReport).filter(SarReport.status == "closed").count()

    # Recent risk events
    last_30d = datetime.utcnow() - timedelta(days=30)
    recent_events = db.query(RiskEvent).filter(RiskEvent.created_at >= last_30d).count()
    critical_events = (
        db.query(RiskEvent)
        .filter(RiskEvent.created_at >= last_30d, RiskEvent.severity == "critical")
        .count()
    )

    return {
        "sar_reports": {
            "total": total_sars,
            "draft": draft,
            "submitted": submitted,
            "under_review": under_review,
            "closed": closed,
        },
        "risk_events": {
            "last_30_days": recent_events,
            "critical": critical_events,
        },
    }
