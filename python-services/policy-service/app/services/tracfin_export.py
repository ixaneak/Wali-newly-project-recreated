"""
TRACFIN Export Service

Generates TRACFIN-compatible SAR (Suspicious Activity Report) XML for
regulatory filing with French financial intelligence unit.

TRACFIN = Traitement du Renseignement et Action Contre les 
          Circuits Financiers Clandestins
"""
from datetime import datetime
from typing import List, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom


def mask_phone(phone: str) -> str:
    """Mask phone for privacy: 07XX XXX XXX"""
    if not phone:
        return "MASKED"
    if len(phone) >= 10:
        return phone[:4] + " XXX " + phone[-3:]
    elif len(phone) >= 8:
        return phone[:2] + "XX XXX " + phone[-2:]
    return "MASKED"


def mask_email(email: str) -> str:
    """Mask email: j***@example.com"""
    if not email or "@" not in email:
        return "MASKED"
    local, domain = email.split("@")
    if len(local) > 1:
        return local[0] + "***@" + domain
    return "***@" + domain


def generate_attachment_refs(documents: List[str]) -> str:
    """Generate XML for supporting document references."""
    if not documents:
        return "<document>None</document>"
    
    xml_parts = []
    for i, doc in enumerate(documents, 1):
        xml_parts.append(f"<document id='{i}'>{doc}</document>")
    return "\n            ".join(xml_parts)


def generate_indicator_xml(indicators: List[dict]) -> str:
    """Generate XML for detection indicators."""
    if not indicators:
        return "<indicator>None</indicator>"
    
    xml_parts = []
    for ind in indicators:
        xml_parts.append(f"""<indicator>
                <type>{ind.get('type', 'unknown')}</type>
                <severity>{ind.get('severity', 'medium')}</severity>
                <description>{ind.get('description', '')}</description>
            </indicator>""")
    return "\n            ".join(xml_parts)


def generate_tracfin_xml(report: dict) -> str:
    """
    Generate TRACFIN-compatible SAR report XML.
    
    Args:
        report: Dictionary containing SAR report data
        
    Returns:
        Formatted XML string ready for TRACFIN submission
    """
    now = datetime.utcnow()
    
    # Build XML using ElementTree for proper escaping
    root = ET.Element("suspicious_activity_report")
    root.set("xmlns", "http://www.tracfin.gouv.fr/sar/1.0")
    root.set("version", "1.0")
    root.set("generated_at", now.isoformat())
    
    # Reporting Entity
    reporting = ET.SubElement(root, "reporting_entity")
    ET.SubElement(reporting, "name").text = "WALI TECHNOLOGY SAS"
    ET.SubElement(reporting, "legal_form").text = "Société par Actions Simplifiée"
    ET.SubElement(reporting, "naf_code").text = "6201Z"
    ET.SubElement(reporting, "activity_description").text = "Activités des sièges sociaux"
    ET.SubElement(reporting, "license_number").text = "CIMA-MICRO-2024-XXXX"
    ET.SubElement(reporting, "siret").text = "XXX XXX XXX XXXXX"
    ET.SubElement(reporting, "report_date").text = now.strftime("%Y-%m-%d")
    ET.SubElement(reporting, "report_type").text = "SAR_INSURANCE"
    
    # Report Reference
    ET.SubElement(root, "report_reference").text = report.get('report_reference', 'UNKNOWN')
    ET.SubElement(root, "report_status").text = report.get('status', 'draft')
    
    # Subject (suspicious person/entity)
    subject = ET.SubElement(root, "subject")
    ET.SubElement(subject, "type").text = report.get('subject_type', 'individual')
    ET.SubElement(subject, "name").text = report.get('subject_name', 'UNKNOWN')
    ET.SubElement(subject, "phone").text = mask_phone(report.get('subject_phone', ''))
    ET.SubElement(subject, "id_number").text = report.get('subject_id', 'UNKNOWN')
    ET.SubElement(subject, "id_type").text = "NATIONAL_ID"
    
    # Activity Details
    activity = ET.SubElement(root, "activity")
    ET.SubElement(activity, "type").text = report.get('activity_type', 'INSURANCE_FRAUD')
    ET.SubElement(activity, "category").text = "MICRO_INSURANCE"
    
    occurrence_date = report.get('occurrence_date')
    if occurrence_date:
        if isinstance(occurrence_date, datetime):
            ET.SubElement(activity, "date").text = occurrence_date.strftime("%Y-%m-%d")
        else:
            ET.SubElement(activity, "date").text = str(occurrence_date)[:10]
    
    amount = ET.SubElement(activity, "amount")
    amount.set("currency", "XOF")
    amount.set("usd_approx", str(int(report.get('amount_involved', 0) / 600)))  # Rough XOF/USD
    amount.text = str(report.get('amount_involved', 0))
    
    ET.SubElement(activity, "description").text = report.get('description', '')
    
    # Location (if available)
    location = ET.SubElement(activity, "location")
    ET.SubElement(location, "country").text = "CI"  # Côte d'Ivoire
    ET.SubElement(location, "region").text = report.get('region', 'UNKNOWN')
    
    # Risk Assessment
    indicators = ET.SubElement(root, "indicators")
    ET.SubElement(indicators, "risk_score").text = str(report.get('risk_score', 0))
    ET.SubElement(indicators, "risk_level").text = _get_risk_level(report.get('risk_score', 0))
    ET.SubElement(indicators, "automation_flag").text = "True"
    ET.SubElement(indicators, "detection_date").text = now.isoformat()
    
    # Triggered Rules
    triggered_rules = report.get('triggered_rules', [])
    rules_elem = ET.SubElement(indicators, "triggered_rules")
    for rule in triggered_rules:
        rule_elem = ET.SubElement(rules_elem, "rule")
        if isinstance(rule, dict):
            ET.SubElement(rule_elem, "name").text = rule.get('rule', 'unknown')
            ET.SubElement(rule_elem, "score").text = str(rule.get('score', 0))
        else:
            ET.SubElement(rule_elem, "name").text = str(rule)
            ET.SubElement(rule_elem, "score").text = "0"
    
    # Related Transactions
    transactions = ET.SubElement(root, "related_transactions")
    related = report.get('related_transactions', [])
    if related:
        for tx in related:
            ET.SubElement(transactions, "transaction_id").text = str(tx)
    else:
        ET.SubElement(transactions, "transaction_id").text = "N/A"
    
    # Supporting Documents
    attachments = ET.SubElement(root, "attachments")
    docs = report.get('supporting_documents', [])
    if docs:
        for i, doc in enumerate(docs, 1):
            doc_elem = ET.SubElement(attachments, "document")
            doc_elem.set("id", str(i))
            doc_elem.set("type", "evidence")
            ET.SubElement(doc_elem, "reference").text = str(doc)
            ET.SubElement(doc_elem, "hash_type").text = "SHA256"
    else:
        ET.SubElement(attachments, "document").text = "None"
    
    # Compliance Notes
    compliance = ET.SubElement(root, "compliance")
    ET.SubElement(compliance, "analyst_reviewed").text = "False"
    ET.SubElement(compliance, "manager_approved").text = "False"
    ET.SubElement(compliance, "retention_years").text = "5"
    ET.SubElement(compliance, "regulatory_framework").text = "CIMA-AML-2024"
    
    # Convert to formatted string
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    
    # Add XML declaration and format
    formatted = reparsed.toprettyxml(indent="    ")
    
    # Remove extra blank lines from minidom
    lines = [line for line in formatted.split('\n') if line.strip()]
    return '\n'.join(lines)


def _get_risk_level(score: int) -> str:
    """Convert numeric score to risk level."""
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"


def validate_tracfin_xml(xml_string: str) -> tuple[bool, List[str]]:
    """
    Validate TRACFIN XML structure.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        return False, [f"XML Parse Error: {e}"]
    
    # Required elements
    required_elements = [
        "reporting_entity",
        "report_reference",
        "subject",
        "activity",
        "indicators"
    ]
    
    for elem in required_elements:
        if root.find(elem) is None:
            errors.append(f"Missing required element: {elem}")
    
    # Validate reporting entity
    reporting = root.find("reporting_entity")
    if reporting is not None:
        if reporting.find("name") is None:
            errors.append("Reporting entity missing name")
        if reporting.find("license_number") is None:
            errors.append("Reporting entity missing license_number")
    
    # Validate subject
    subject = root.find("subject")
    if subject is not None:
        if subject.find("type") is None:
            errors.append("Subject missing type")
        if subject.find("name") is None:
            errors.append("Subject missing name")
    
    # Validate activity
    activity = root.find("activity")
    if activity is not None:
        if activity.find("type") is None:
            errors.append("Activity missing type")
        if activity.find("amount") is None:
            errors.append("Activity missing amount")
    
    return len(errors) == 0, errors


def generate_tracfin_batch_xml(reports: List[dict]) -> str:
    """
    Generate batch TRACFIN XML for multiple reports.
    
    Args:
        reports: List of SAR report dictionaries
        
    Returns:
        Formatted XML string containing all reports
    """
    now = datetime.utcnow()
    
    root = ET.Element("suspicious_activity_batch")
    root.set("xmlns", "http://www.tracfin.gouv.fr/sar/1.0")
    root.set("version", "1.0")
    root.set("generated_at", now.isoformat())
    root.set("count", str(len(reports)))
    
    # Batch metadata
    metadata = ET.SubElement(root, "batch_metadata")
    ET.SubElement(metadata, "reporting_entity").text = "WALI TECHNOLOGY SAS"
    ET.SubElement(metadata, "license_number").text = "CIMA-MICRO-2024-XXXX"
    ET.SubElement(metadata, "submission_date").text = now.strftime("%Y-%m-%d")
    ET.SubElement(metadata, "report_count").text = str(len(reports))
    
    # Individual reports (as string to embed)
    reports_elem = ET.SubElement(root, "reports")
    
    for report in reports:
        # Generate individual report
        individual_xml = generate_tracfin_xml(report)
        # Parse and append
        individual_root = ET.fromstring(individual_xml)
        reports_elem.append(individual_root)
    
    # Format output
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    formatted = reparsed.toprettyxml(indent="    ")
    lines = [line for line in formatted.split('\n') if line.strip()]
    return '\n'.join(lines)
