"""Compliance service for COSUMAF reporting and audit trails."""
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List
from lxml import etree
import logging

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for managing compliance and audit trails."""
    
    @staticmethod
    def create_financial_event(
        db: Session,
        event_type: str,
        amount: int,
        segregated_escrow: bool,
        transaction_id: str = None,
        policy_id: str = None,
        claim_id: str = None,
        user_id: str = None,
        metadata: dict = None
    ) -> Dict:
        """
        Create immutable financial event with SHA-256 chain hashing.
        
        Args:
            db: Database session
            event_type: Type of event (premium_collected, claim_paid, tech_fee, refund)
            amount: Amount in XOF
            segregated_escrow: True for premiums (escrow), False for tech fees (operating)
            transaction_id, policy_id, claim_id, user_id: Optional references
            metadata: Optional additional data
        
        Returns:
            Created financial event dict
        """
        # Get previous hash for chain
        previous_hash = ComplianceService._get_latest_hash(db)
        
        # Calculate compliance hash
        event_data = f"{event_type}{amount}{segregated_escrow}{transaction_id}{datetime.now().isoformat()}{previous_hash}"
        compliance_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Determine escrow account
        escrow_account = "ESCROW_ACCOUNT" if segregated_escrow else "OPERATING_ACCOUNT"
        
        # Insert into financial_events table
        query = text("""
            INSERT INTO financial_events (
                event_type, amount, segregated_escrow, escrow_account,
                transaction_id, policy_id, claim_id, user_id,
                previous_hash, compliance_hash, metadata
            )
            VALUES (
                :event_type, :amount, :segregated_escrow, :escrow_account,
                :transaction_id, :policy_id, :claim_id, :user_id,
                :previous_hash, :compliance_hash, :metadata
            )
            RETURNING id, created_at
        """)
        
        result = db.execute(query, {
            "event_type": event_type,
            "amount": amount,
            "segregated_escrow": segregated_escrow,
            "escrow_account": escrow_account,
            "transaction_id": transaction_id,
            "policy_id": policy_id,
            "claim_id": claim_id,
            "user_id": user_id,
            "previous_hash": previous_hash,
            "compliance_hash": compliance_hash,
            "metadata": metadata
        })
        
        row = result.fetchone()
        db.commit()
        
        logger.info(f"Financial event created: {event_type}, Amount: {amount}, Hash: {compliance_hash[:16]}...")
        
        return {
            "id": str(row.id),
            "event_type": event_type,
            "amount": amount,
            "compliance_hash": compliance_hash,
            "created_at": row.created_at.isoformat()
        }
    
    @staticmethod
    def _get_latest_hash(db: Session) -> str:
        """Get the latest compliance hash for chain integrity."""
        query = text("""
            SELECT compliance_hash 
            FROM financial_events 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        result = db.execute(query)
        row = result.fetchone()
        return row.compliance_hash if row else "GENESIS_HASH"
    
    @staticmethod
    def verify_hash_chain(db: Session) -> Dict:
        """Verify the integrity of the financial events hash chain."""
        query = text("""
            SELECT id, event_type, amount, previous_hash, compliance_hash, created_at
            FROM financial_events
            ORDER BY created_at ASC
        """)
        
        events = db.execute(query).fetchall()
        
        valid = True
        broken_links = []
        expected_previous = "GENESIS_HASH"
        
        for event in events:
            if event.previous_hash != expected_previous:
                valid = False
                broken_links.append({
                    "event_id": str(event.id),
                    "expected": expected_previous,
                    "actual": event.previous_hash
                })
            
            expected_previous = event.compliance_hash
        
        return {
            "valid": valid,
            "total_events": len(events),
            "broken_links": broken_links
        }
    
    @staticmethod
    def generate_cosumaf_monthly_report(
        db: Session,
        year: int,
        month: int
    ) -> str:
        """
        Generate COSUMAF-compliant monthly XML report.
        
        Args:
            db: Database session
            year: Report year
            month: Report month (1-12)
        
        Returns:
            XML string in UEMOA format
        """
        # Date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Query financial events for the month
        query = text("""
            SELECT 
                event_type,
                SUM(amount) as total_amount,
                COUNT(*) as count,
                segregated_escrow
            FROM financial_events
            WHERE created_at >= :start_date AND created_at < :end_date
            GROUP BY event_type, segregated_escrow
        """)
        
        results = db.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        }).fetchall()
        
        # Build XML report (UEMOA format)
        root = etree.Element("COSUMAFReport", version="1.0")
        
        # Header
        header = etree.SubElement(root, "Header")
        etree.SubElement(header, "ReportDate").text = datetime.now().isoformat()
        etree.SubElement(header, "ReportingPeriod").text = f"{year}-{month:02d}"
        etree.SubElement(header, "Jurisdiction").text = "Côte d'Ivoire"
        etree.SubElement(header, "CompanyName").text = "Wali Micro-Insurance"
        
        # Financial Summary
        summary = etree.SubElement(root, "FinancialSummary")
        
        total_premiums = 0
        total_claims = 0
        total_tech_fees = 0
        
        for row in results:
            if row.event_type == "premium_collected":
                total_premiums += row.total_amount
            elif row.event_type == "claim_paid":
                total_claims += row.total_amount
            elif row.event_type == "tech_fee":
                total_tech_fees += row.total_amount
        
        etree.SubElement(summary, "TotalPremiumsCollected").text = str(total_premiums)
        etree.SubElement(summary, "TotalClaimsPaid").text = str(total_claims)
        etree.SubElement(summary, "TotalTechFees").text = str(total_tech_fees)
        etree.SubElement(summary, "Currency").text = "XOF"
        
        # Event details
        events = etree.SubElement(root, "EventDetails")
        for row in results:
            event = etree.SubElement(events, "Event")
            etree.SubElement(event, "Type").text = row.event_type
            etree.SubElement(event,  "TotalAmount").text = str(row.total_amount)
            etree.SubElement(event, "Count").text = str(row.count)
            etree.SubElement(event, "EscrowSegregated").text = str(row.segregated_escrow)
        
        # Convert to XML string
        xml_string = etree.tostring(
            root, 
            pretty_print=True, 
            xml_declaration=True, 
            encoding='UTF-8'
        ).decode('utf-8')
        
        logger.info(f"Generated COSUMAF report for {year}-{month:02d}")
        
        return xml_string
    
    @staticmethod
    def get_tax_exemption_status(db: Session, start_date: str = "2026-01-01") -> Dict:
        """
        Track 3-year tax exemption countdown.
        
        Args:
            db: Database session
            start_date: Tax exemption start date (ISO format)
        
        Returns:
            Tax exemption status dict
        """
        start_dt = datetime.fromisoformat(start_date)
        end_dt = start_dt + timedelta(days=365 * 3)  # 3 years
        now = datetime.now()
        
        days_remaining = (end_dt - now).days
        days_elapsed = (now - start_dt).days
        
        # Calculate segregated revenue
        query = text("""
            SELECT 
                SUM(CASE WHEN segregated_escrow = true THEN amount ELSE 0 END) as escrow_total,
                SUM(CASE WHEN segregated_escrow = false THEN amount ELSE 0 END) as operating_total
            FROM financial_events
            WHERE event_type IN ('premium_collected', 'tech_fee')
        """)
        
        result = db.execute(query).fetchone()
        
        return {
            "start_date": start_date,
            "end_date": end_dt.isoformat(),
            "days_elapsed": days_elapsed,
            "days_remaining": max(0, days_remaining),
            "percentage_complete": min(100, int((days_elapsed / (365 * 3)) * 100)),
            "active": days_remaining > 0,
            "escrow_revenue_total": result.escrow_total or 0,
            "operating_revenue_total": result.operating_total or 0,
            "tech_fee_percentage": 2
        }
