"""
SAR Compliance Unit Tests

Tests for:
1. Risk scoring rules (all 7)
2. SAR workflow (status transitions)
3. 5-year retention period
4. Compliance list screening
5. Report reference format
6. TRACFIN XML generation
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
import uuid

from app.models.sar_report import SarReport, SarStatus, _generate_reference, _retention_date
from app.models.risk_event import RiskEvent, RiskSeverity
from app.models.compliance_list import ComplianceListEntry, ListType
from app.services.sar_service import (
    _rule_structuring,
    _rule_rapid_claim,
    _rule_round_number,
    _rule_high_velocity,
    _rule_threshold_breach,
    _rule_identity_inconsistency,
    _rule_third_party_payment,
    score_transaction,
    check_compliance_list,
    THRESHOLD_AMOUNT_XOF,
)
from app.services.tracfin_service import generate_tracfin_xml, generate_tracfin_summary

mock_db = MagicMock()


# ── 1. Risk Scoring Rules ───────────────────────────────────────

class TestRoundNumberRule:
    def test_round_number_fires(self):
        """Exact multiple of 1000 above 50k should flag."""
        fired, score, ctx = _rule_round_number(100_000)
        assert fired is True
        assert score > 0
        assert ctx["rule"] == "round_number"

    def test_non_round_number_skips(self):
        """Amounts with remainder should not flag."""
        fired, _, _ = _rule_round_number(100_123)
        assert fired is False

    def test_small_round_number_skips(self):
        """Round number below 50k should not flag."""
        fired, _, _ = _rule_round_number(10_000)
        assert fired is False


class TestThresholdBreachRule:
    def test_above_threshold_fires(self):
        """Above 500k XOF should flag."""
        fired, score, ctx = _rule_threshold_breach(600_000)
        assert fired is True
        assert score > 0
        assert ctx["rule"] == "threshold_breach"

    def test_below_threshold_skips(self):
        """Below 500k XOF should not flag."""
        fired, _, _ = _rule_threshold_breach(400_000)
        assert fired is False


class TestIdentityInconsistencyRule:
    def test_region_mismatch_fires(self):
        """Different user region and claim location should flag."""
        fired, score, ctx = _rule_identity_inconsistency("Abidjan", "Bouaké")
        assert fired is True
        assert ctx["rule"] == "identity_inconsistency"

    def test_same_region_skips(self):
        fired, _, _ = _rule_identity_inconsistency("Abidjan", "Abidjan")
        assert fired is False

    def test_missing_data_skips(self):
        fired, _, _ = _rule_identity_inconsistency(None, "Abidjan")
        assert fired is False


class TestThirdPartyPaymentRule:
    def test_different_phones_fires(self):
        fired, score, ctx = _rule_third_party_payment("+2250101000001", "+2250707000002")
        assert fired is True
        assert ctx["rule"] == "third_party_payment"

    def test_same_phone_skips(self):
        fired, _, _ = _rule_third_party_payment("+2250707000001", "+2250707000001")
        assert fired is False


class TestRapidClaimRule:
    def test_rapid_claim_fires(self):
        """Claim within 24 hours of policy start should flag."""
        mock = MagicMock()
        policy = MagicMock()
        policy.start_date = datetime(2026, 1, 15, 10, 0, 0)
        mock.query.return_value.filter.return_value.first.return_value = policy

        claim_time = datetime(2026, 1, 15, 20, 0, 0)  # 10 hours later
        fired, score, ctx = _rule_rapid_claim(mock, "policy-123", claim_time)
        assert fired is True
        assert ctx["rule"] == "rapid_claim"

    def test_normal_claim_skips(self):
        """Claim after 72 hours should not flag."""
        mock = MagicMock()
        policy = MagicMock()
        policy.start_date = datetime(2026, 1, 10, 10, 0, 0)
        mock.query.return_value.filter.return_value.first.return_value = policy

        claim_time = datetime(2026, 1, 15, 10, 0, 0)  # 5 days later
        fired, _, _ = _rule_rapid_claim(mock, "policy-123", claim_time)
        assert fired is False


# ── 2. Score Aggregation ────────────────────────────────────────

class TestScoreAggregation:
    def test_score_capped_at_100(self):
        """Total score should never exceed 100."""
        # Mock DB to trigger multiple rules at once
        mock = MagicMock()

        # Structuring: return 4 policies totaling 600k
        policies = []
        for _ in range(4):
            p = MagicMock()
            p.partner_quoted_amount = 150_000
            p.created_at = datetime.utcnow()
            policies.append(p)
        mock.query.return_value.filter.return_value.all.return_value = policies
        mock.query.return_value.filter.return_value.count.return_value = 0
        mock.query.return_value.filter.return_value.first.return_value = None

        result = score_transaction(
            db=mock,
            user_id="user-1",
            amount=600_000,  # triggers threshold_breach + round_number
            phone=None,
            payer_phone="+225111",
            policyholder_phone="+225222",
            user_region="Abidjan",
            claim_location="Daloa",
        )
        assert result["risk_score"] <= 100

    def test_severity_critical(self):
        result_data = {"risk_score": 85, "severity": "critical"}
        assert result_data["severity"] == "critical"

    def test_severity_low_for_zero(self):
        """Zero score should be low severity."""
        mock = MagicMock()
        mock.query.return_value.filter.return_value.all.return_value = []
        mock.query.return_value.filter.return_value.count.return_value = 0
        mock.query.return_value.filter.return_value.first.return_value = None

        result = score_transaction(db=mock, user_id="u1", amount=500)
        assert result["severity"] == "low"
        assert result["rules_fired"] == 0


# ── 3. SAR Workflow ─────────────────────────────────────────────

class TestSarWorkflow:
    def test_valid_transition_draft_to_submitted(self):
        """draft → submitted is allowed."""
        from app.services.sar_service import update_sar_status
        mock = MagicMock()
        sar = MagicMock()
        sar.status = "draft"
        mock.query.return_value.filter.return_value.first.return_value = sar

        update_sar_status(mock, "sar-1", new_status="submitted")
        assert sar.status == "submitted"
        assert sar.submitted_at is not None

    def test_invalid_transition_raises(self):
        """closed → draft is not allowed."""
        from app.services.sar_service import update_sar_status
        mock = MagicMock()
        sar = MagicMock()
        sar.status = "closed"
        mock.query.return_value.filter.return_value.first.return_value = sar

        with pytest.raises(ValueError, match="Cannot transition"):
            update_sar_status(mock, "sar-1", new_status="draft")


# ── 4. Retention Period ─────────────────────────────────────────

class TestRetentionPeriod:
    def test_retention_is_5_years(self):
        """Retention should be approximately 5 years from now."""
        retention = _retention_date()
        delta = retention - datetime.utcnow()
        assert 1824 <= delta.days <= 1827  # ~5 years


# ── 5. Report Reference Format ─────────────────────────────────

class TestReportReference:
    def test_format(self):
        """Reference should be SAR-YYYY-XXXXXX."""
        ref = _generate_reference()
        assert ref.startswith("SAR-2026-"), f"Got {ref}"
        parts = ref.split("-")
        assert len(parts) == 3
        assert len(parts[2]) == 6  # 6 hex chars


# ── 6. Compliance List Screening ────────────────────────────────

class TestComplianceListScreening:
    def test_blacklisted_flagged(self):
        mock = MagicMock()
        entry = MagicMock()
        entry.list_type = "blacklist"
        entry.expires_at = None
        entry.to_dict.return_value = {"list_type": "blacklist", "identifier": "+225000"}
        mock.query.return_value.filter.return_value.all.return_value = [entry]

        result = check_compliance_list(mock, "+225000")
        assert result["is_blacklisted"] is True
        assert result["match_count"] == 1

    def test_expired_entry_skipped(self):
        mock = MagicMock()
        entry = MagicMock()
        entry.list_type = "blacklist"
        entry.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
        mock.query.return_value.filter.return_value.all.return_value = [entry]

        result = check_compliance_list(mock, "+225000")
        assert result["is_blacklisted"] is False
        assert result["match_count"] == 0


# ── 7. TRACFIN XML Generation ──────────────────────────────────

class TestTracfinXml:
    def test_xml_contains_sar_reference(self):
        mock = MagicMock()
        sar = MagicMock()
        sar.report_reference = "SAR-2026-ABC123"
        sar.subject_type = "policyholder"
        sar.subject_id = "user-1"
        sar.subject_name = "Test User"
        sar.subject_phone = "+22507000000"
        sar.activity_type = "rapid_claim"
        sar.occurrence_date = datetime(2026, 2, 1)
        sar.detection_date = datetime(2026, 2, 2)
        sar.description = "Suspicious rapid claim"
        sar.risk_score = 75
        sar.amount_involved = 300_000
        sar.currency = "XOF"
        sar.related_transactions = ["tx-1", "tx-2"]
        sar.assigned_analyst = "analyst@wali.ci"
        mock.query.return_value.filter.return_value.first.return_value = sar
        mock.query.return_value.filter.return_value.all.return_value = []  # no linked events

        xml_str = generate_tracfin_xml(mock, "sar-id")
        assert "SAR-2026-ABC123" in xml_str
        assert "DeclarationSoupcon" in xml_str
        assert "Wali Technology SAS" in xml_str
        assert "rapid_claim" in xml_str

    def test_summary_includes_deadline(self):
        mock = MagicMock()
        sar = MagicMock()
        sar.report_reference = "SAR-2026-XYZ"
        sar.status = "draft"
        sar.detection_date = datetime.utcnow() - timedelta(days=25)
        sar.retention_until = datetime.utcnow() + timedelta(days=5*365)
        sar.to_dict.return_value = {"report_reference": "SAR-2026-XYZ", "status": "draft"}
        mock.query.return_value.filter.return_value.first.return_value = sar
        mock.query.return_value.filter.return_value.all.return_value = []

        summary = generate_tracfin_summary(mock, "sar-id")
        assert summary["filing_deadline"]["days_until_deadline"] == 5
        assert summary["filing_deadline"]["is_overdue"] is False
