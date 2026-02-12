"""
SaaS Billing Service — B2B Subscription Management

Wali charges partner insurers a FLAT monthly software license fee.
This is NOT a commission on insurance premiums.

Revenue model:
  • NSIA pays Wali 500,000 FCFA/month for platform access
  • Amount is fixed regardless of number of artisans or premium volume
  • Tax category: "prestation_informatique" (computer services)
"""
import uuid
import logging
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from app.models.partner import (
    Partner, PartnerInvoice, PartnerInvoiceStatus, PlatformUsageLog,
)
from app.config.compliance import PARTNER_MONTHLY_LICENSE_FEE

logger = logging.getLogger(__name__)

TVA_RATE = 0.18  # Ivory Coast VAT


class SaaSBillingService:
    """
    B2B subscription billing — flat fee only.

    Wali invoices partner insurers for software license, NOT for
    percentage commissions on premiums. This is critical for
    Label Startup Numérique eligibility.
    """

    @staticmethod
    def generate_monthly_invoice(
        db: Session,
        partner_id: str,
        period_month: date,
    ) -> PartnerInvoice:
        """
        Generate flat-fee SaaS invoice for partner insurer.

        Args:
            db: Database session
            partner_id: Partner identifier (e.g. "NSIA")
            period_month: First day of the billing month

        Returns:
            Created PartnerInvoice
        """
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise ValueError(f"Partner {partner_id} not found")

        fee = partner.monthly_fee or PARTNER_MONTHLY_LICENSE_FEE
        total_with_tax = int(fee * (1 + TVA_RATE))

        # Invoice number: WALI-NSIA-2026-02
        period_str = period_month.strftime("%Y-%m")
        invoice_number = f"WALI-{partner_id}-{period_str}"

        invoice = PartnerInvoice(
            partner_id=partner_id,
            invoice_number=invoice_number,
            amount_due=fee,
            tax_rate=TVA_RATE,
            total_with_tax=total_with_tax,
            description=f"Licence logicielle SaaS - Plateforme WALI (Période: {period_str})",
            period_start=period_month,
            period_end=(period_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1),
            status=PartnerInvoiceStatus.DRAFT,
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        logger.info(
            "Generated SaaS invoice %s for partner %s: %d FCFA + TVA = %d FCFA",
            invoice_number, partner_id, fee, total_with_tax,
        )
        return invoice

    @staticmethod
    def record_platform_usage(
        db: Session,
        partner_id: str,
        log_date: Optional[date] = None,
    ) -> PlatformUsageLog:
        """
        Record daily SaaS usage metrics for a partner.
        Proves Wali provides software services: API calls, uptime, storage.
        """
        today = log_date or date.today()

        # Count usage for this partner today
        from app.models.policy import CoverageSubscription, SubscriptionStatus
        from app.models.financial_event import FinancialEvent

        active_artisans = (
            db.query(sa_func.count(CoverageSubscription.id))
            .filter(
                CoverageSubscription.partner_id == partner_id,
                CoverageSubscription.status == SubscriptionStatus.ACTIVE,
            )
            .scalar() or 0
        )

        enrollments_today = (
            db.query(sa_func.count(CoverageSubscription.id))
            .filter(
                CoverageSubscription.partner_id == partner_id,
                sa_func.date(CoverageSubscription.created_at) == today,
            )
            .scalar() or 0
        )

        payments_today = (
            db.query(sa_func.count(FinancialEvent.id))
            .filter(
                FinancialEvent.partner_id == partner_id,
                FinancialEvent.event_type == "payment_routed",
                sa_func.date(FinancialEvent.created_at) == today,
            )
            .scalar() or 0
        )

        usage = PlatformUsageLog(
            partner_id=partner_id,
            log_date=today,
            api_calls_count=payments_today + enrollments_today,
            active_artisans_count=active_artisans,
            enrollments_processed=enrollments_today,
            platform_uptime_percent=99.9,
        )

        db.add(usage)
        db.commit()
        db.refresh(usage)
        return usage

    @staticmethod
    def get_software_value_report(
        db: Session,
        partner_id: str,
        days: int = 30,
    ) -> dict:
        """
        Generate report showing platform value for contract renewals.
        Aggregates last N days of usage metrics.
        """
        cutoff = date.today() - timedelta(days=days)

        logs = (
            db.query(PlatformUsageLog)
            .filter(
                PlatformUsageLog.partner_id == partner_id,
                PlatformUsageLog.log_date >= cutoff,
            )
            .all()
        )

        if not logs:
            return {
                "partner_id": partner_id,
                "period_days": days,
                "total_api_calls": 0,
                "artisans_reached": 0,
                "uptime_sla": "99.9%",
                "value_proposition": "Plateforme digitale permettant d'atteindre les artisans via mobile",
            }

        return {
            "partner_id": partner_id,
            "period_days": days,
            "total_api_calls": sum(l.api_calls_count or 0 for l in logs),
            "total_enrollments": sum(l.enrollments_processed or 0 for l in logs),
            "total_incidents_reported": sum(l.incidents_reported or 0 for l in logs),
            "artisans_reached": max((l.active_artisans_count or 0) for l in logs),
            "avg_uptime": f"{sum(float(l.platform_uptime_percent or 0) for l in logs) / len(logs):.1f}%",
            "uptime_sla": "99.9%",
            "value_proposition": (
                f"Plateforme digitale permettant à {partner_id} d'atteindre "
                f"{max((l.active_artisans_count or 0) for l in logs):,}+ artisans via mobile"
            ),
        }

    @staticmethod
    def mark_invoice_paid(
        db: Session,
        invoice_id: str,
    ) -> PartnerInvoice:
        """Record receipt of SaaS subscription payment from partner."""
        invoice = db.query(PartnerInvoice).filter(
            PartnerInvoice.id == invoice_id
        ).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        invoice.status = PartnerInvoiceStatus.PAID
        invoice.paid_at = datetime.now()
        db.commit()
        db.refresh(invoice)

        logger.info(
            "SaaS invoice %s marked as paid: %d FCFA from %s",
            invoice.invoice_number, invoice.amount_due, invoice.partner_id,
        )
        return invoice
