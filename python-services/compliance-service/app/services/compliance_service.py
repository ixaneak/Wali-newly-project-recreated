"""
Compliance service — SaaS platform reporting and audit trails.

Wali is a B2B SaaS software vendor (NAF 6201Z).
We generate platform reports, NOT COSUMAF insurance reports.
"""
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict
from lxml import etree
import logging

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for SaaS platform compliance and audit trails."""

    @staticmethod
    def create_financial_event(
        db: Session,
        event_type: str,
        amount: int,
        routed_to_partner: bool,
        transaction_id: str = None,
        subscription_id: str = None,
        partner_id: str = None,
        user_id: str = None,
        metadata: dict = None,
    ) -> Dict:
        """
        Create immutable financial event with SHA-256 chain hashing.

        Args:
            event_type: payment_routed, claim_forwarded, saas_fee_received, tech_fee
            amount: Amount in XOF
            routed_to_partner: True if payment went to partner insurer
            transaction_id, subscription_id, partner_id, user_id: references
        """
        previous_hash = ComplianceService._get_latest_hash(db)

        event_data = f"{event_type}{amount}{routed_to_partner}{transaction_id}{datetime.now().isoformat()}{previous_hash}"
        compliance_hash = hashlib.sha256(event_data.encode()).hexdigest()

        query = text("""
            INSERT INTO financial_events (
                event_type, amount, routed_to_partner,
                transaction_id, subscription_id, partner_id, user_id,
                wali_role, previous_hash, compliance_hash
            )
            VALUES (
                :event_type, :amount, :routed_to_partner,
                :transaction_id, :subscription_id, :partner_id, :user_id,
                'technology_provider', :previous_hash, :compliance_hash
            )
            RETURNING id, created_at
        """)

        result = db.execute(query, {
            "event_type": event_type,
            "amount": amount,
            "routed_to_partner": routed_to_partner,
            "transaction_id": transaction_id,
            "subscription_id": subscription_id,
            "partner_id": partner_id,
            "user_id": user_id,
            "previous_hash": previous_hash,
            "compliance_hash": compliance_hash,
        })

        row = result.fetchone()
        db.commit()

        logger.info(f"Financial event: {event_type}, Amount: {amount}, Partner: {partner_id}")

        return {
            "id": str(row.id),
            "event_type": event_type,
            "amount": amount,
            "compliance_hash": compliance_hash,
            "wali_role": "technology_provider",
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _get_latest_hash(db: Session) -> str:
        query = text("SELECT compliance_hash FROM financial_events ORDER BY created_at DESC LIMIT 1")
        result = db.execute(query)
        row = result.fetchone()
        return row.compliance_hash if row else "GENESIS_HASH"

    @staticmethod
    def verify_hash_chain(db: Session) -> Dict:
        query = text("""
            SELECT id, event_type, amount, previous_hash, compliance_hash, created_at
            FROM financial_events ORDER BY created_at ASC
        """)
        events = db.execute(query).fetchall()

        valid = True
        broken_links = []
        expected_previous = "GENESIS_HASH"

        for event in events:
            if event.previous_hash != expected_previous:
                valid = False
                broken_links.append({"event_id": str(event.id), "expected": expected_previous, "actual": event.previous_hash})
            expected_previous = event.compliance_hash

        return {"valid": valid, "total_events": len(events), "broken_links": broken_links}

    @staticmethod
    def generate_platform_monthly_report(db: Session, year: int, month: int) -> str:
        """
        Generate SaaS platform monthly report (XML).

        NOT a COSUMAF report — Wali is not an insurer.
        """
        start_date = datetime(year, month, 1)
        end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

        query = text("""
            SELECT event_type, SUM(amount) as total_amount, COUNT(*) as count, routed_to_partner
            FROM financial_events
            WHERE created_at >= :start_date AND created_at < :end_date
            GROUP BY event_type, routed_to_partner
        """)
        results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()

        root = etree.Element("PlatformReport", version="2.0")

        header = etree.SubElement(root, "Header")
        etree.SubElement(header, "ReportDate").text = datetime.now().isoformat()
        etree.SubElement(header, "ReportingPeriod").text = f"{year}-{month:02d}"
        etree.SubElement(header, "PlatformModel").text = "B2B_SAAS"
        etree.SubElement(header, "CompanyName").text = "Wali SaaS Platform"
        etree.SubElement(header, "NAFCode").text = "6201Z"
        etree.SubElement(header, "WaliRole").text = "technology_provider"

        summary = etree.SubElement(root, "RevenueSummary")

        total_routed = 0
        total_saas = 0
        total_incidents = 0

        for row in results:
            if row.event_type == "payment_routed":
                total_routed += row.total_amount
            elif row.event_type == "saas_fee_received":
                total_saas += row.total_amount
            elif row.event_type == "claim_forwarded":
                total_incidents += row.count

        etree.SubElement(summary, "SaaS_Revenue").text = str(total_saas)
        etree.SubElement(summary, "Payments_Routed_To_Partners").text = str(total_routed)
        etree.SubElement(summary, "Incidents_Forwarded").text = str(total_incidents)
        etree.SubElement(summary, "Currency").text = "XOF"

        events_el = etree.SubElement(root, "EventDetails")
        for row in results:
            event = etree.SubElement(events_el, "Event")
            etree.SubElement(event, "Type").text = row.event_type
            etree.SubElement(event, "TotalAmount").text = str(row.total_amount)
            etree.SubElement(event, "Count").text = str(row.count)
            etree.SubElement(event, "RoutedToPartner").text = str(row.routed_to_partner)

        xml_string = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode("utf-8")
        logger.info(f"Generated platform report for {year}-{month:02d}")
        return xml_string

    @staticmethod
    def get_tax_exemption_status(db: Session, start_date: str = "2026-01-01") -> Dict:
        """Track 3-year tax exemption countdown for Label Startup."""
        start_dt = datetime.fromisoformat(start_date)
        end_dt = start_dt + timedelta(days=365 * 3)
        now = datetime.now()

        days_remaining = (end_dt - now).days
        days_elapsed = (now - start_dt).days

        query = text("""
            SELECT
                SUM(CASE WHEN routed_to_partner = true THEN amount ELSE 0 END) as routed_total,
                SUM(CASE WHEN event_type = 'saas_fee_received' THEN amount ELSE 0 END) as saas_total,
                SUM(CASE WHEN event_type = 'tech_fee' THEN amount ELSE 0 END) as tech_total
            FROM financial_events
        """)
        result = db.execute(query).fetchone()

        return {
            "start_date": start_date,
            "end_date": end_dt.isoformat(),
            "days_elapsed": days_elapsed,
            "days_remaining": max(0, days_remaining),
            "percentage_complete": min(100, int((days_elapsed / (365 * 3)) * 100)),
            "active": days_remaining > 0,
            "payments_routed_total": result.routed_total or 0,
            "saas_revenue_total": result.saas_total or 0,
            "platform_service_total": result.tech_total or 0,
            "platform_model": "B2B_SAAS",
            "wali_role": "technology_provider",
        }
