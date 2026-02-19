"""
TRACFIN Report Service

Generates XML/summary reports for TRACFIN (Ivory Coast Financial Intelligence Unit).
Reports must be filed within 30 days of detection per CIMA requirements.
"""
from datetime import datetime
from typing import Optional
import logging
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

from sqlalchemy.orm import Session
from app.models.sar_report import SarReport
from app.models.risk_event import RiskEvent

logger = logging.getLogger(__name__)


def generate_tracfin_xml(db: Session, sar_id: str) -> str:
    """
    Generate TRACFIN-format XML report for a SAR.
    Returns the XML string.
    """
    sar = db.query(SarReport).filter(SarReport.id == sar_id).first()
    if not sar:
        raise ValueError(f"SAR report {sar_id} not found")

    # Get linked risk events
    risk_events = (
        db.query(RiskEvent)
        .filter(RiskEvent.sar_report_id == sar_id)
        .all()
    )

    # Build XML
    root = Element("DeclarationSoupcon")
    root.set("version", "1.0")
    root.set("schema", "TRACFIN-CI-2024")

    # Header
    header = SubElement(root, "Header")
    SubElement(header, "Reference").text = sar.report_reference
    SubElement(header, "DateDeclaration").text = datetime.utcnow().strftime("%Y-%m-%d")
    SubElement(header, "TypeOrganisme").text = "TECH_SAAS"
    SubElement(header, "NomOrganisme").text = "Wali Technology SAS"
    SubElement(header, "PaysOrganisme").text = "CI"  # Côte d'Ivoire

    # Declarant
    declarant = SubElement(root, "Declarant")
    SubElement(declarant, "Identifiant").text = sar.assigned_analyst or "SYSTEM"
    SubElement(declarant, "Fonction").text = "Compliance Officer"

    # Subject
    sujet = SubElement(root, "PersonneSoupconnee")
    SubElement(sujet, "TypeSujet").text = sar.subject_type
    SubElement(sujet, "Identifiant").text = sar.subject_id
    if sar.subject_name:
        SubElement(sujet, "Nom").text = sar.subject_name
    if sar.subject_phone:
        SubElement(sujet, "Telephone").text = sar.subject_phone

    # Suspicious activity
    activite = SubElement(root, "ActiviteSuspecte")
    SubElement(activite, "TypeActivite").text = sar.activity_type
    SubElement(activite, "DateOccurrence").text = (
        sar.occurrence_date.strftime("%Y-%m-%d") if sar.occurrence_date else ""
    )
    SubElement(activite, "DateDetection").text = (
        sar.detection_date.strftime("%Y-%m-%d") if sar.detection_date else ""
    )
    SubElement(activite, "Description").text = sar.description
    SubElement(activite, "ScoreRisque").text = str(sar.risk_score or 0)

    # Financial details
    finance = SubElement(root, "DetailFinancier")
    SubElement(finance, "MontantImplique").text = str(sar.amount_involved or 0)
    SubElement(finance, "Devise").text = sar.currency or "XOF"

    if sar.related_transactions:
        transactions = SubElement(finance, "TransactionsLiees")
        for tx_id in sar.related_transactions:
            if tx_id:
                SubElement(transactions, "TransactionId").text = str(tx_id)

    # Linked risk events
    if risk_events:
        evenements = SubElement(root, "EvenementsRisque")
        for evt in risk_events:
            evt_el = SubElement(evenements, "Evenement")
            SubElement(evt_el, "Id").text = str(evt.id)
            SubElement(evt_el, "Type").text = evt.event_type
            SubElement(evt_el, "Severite").text = evt.severity
            SubElement(evt_el, "Score").text = str(evt.risk_score or 0)
            if evt.triggered_rules:
                rules_el = SubElement(evt_el, "ReglesDeclenchees")
                for rule in evt.triggered_rules:
                    SubElement(rules_el, "Regle").text = rule.get("rule", "unknown")

    # Pretty-print
    rough = tostring(root, encoding="unicode")
    dom = parseString(rough)
    return dom.toprettyxml(indent="  ", encoding=None)


def generate_tracfin_summary(db: Session, sar_id: str) -> dict:
    """
    Generate a summary dict for API responses.
    """
    sar = db.query(SarReport).filter(SarReport.id == sar_id).first()
    if not sar:
        raise ValueError(f"SAR report {sar_id} not found")

    risk_events = (
        db.query(RiskEvent)
        .filter(RiskEvent.sar_report_id == sar_id)
        .all()
    )

    # Check if filing deadline is approaching (30 days from detection)
    days_since_detection = (datetime.utcnow() - sar.detection_date).days if sar.detection_date else 0
    days_until_deadline = max(0, 30 - days_since_detection)

    return {
        "sar": sar.to_dict(),
        "linked_risk_events": [e.to_dict() for e in risk_events],
        "filing_deadline": {
            "days_since_detection": days_since_detection,
            "days_until_deadline": days_until_deadline,
            "is_overdue": days_until_deadline == 0 and sar.status == "draft",
            "deadline_date": (
                (sar.detection_date + __import__("datetime").timedelta(days=30)).isoformat()
                if sar.detection_date else None
            ),
        },
        "retention_until": sar.retention_until.isoformat() if sar.retention_until else None,
    }
