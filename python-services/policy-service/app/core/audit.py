import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request

# Configure a specific logger for audit events
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# File handler for local audit trail (log rotation recommended in prod)
# in production, this should be piped to Cloud Logging / Splunk
handler = logging.FileHandler("audit.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
audit_logger.addHandler(handler)

async def log_audit_event(
    action: str,
    outcome: str,
    resource: str,
    user_id: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    request: Optional[Request] = None
):
    """
    Log an immutable audit event for COSUMAF compliance.
    
    Fields:
    - action: What happened (e.g., "CLAIM_SUBMISSION", "LOGIN_ATTEMPT")
    - outcome: "SUCCESS", "FAILURE", "DENIED"
    - resource: Target resource ID (e.g., claim_id, policy_id)
    - user_id: Actor ID
    - detail: JSON-serializable context
    - ip_address: specific IP (or extracted from request)
    """
    
    # Extract context if request provided
    if request and not ip_address:
        ip_address = request.client.host if request.client else "unknown"
        
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "outcome": outcome,
        "resource": resource,
        "user_id": user_id or "anonymous",
        "ip_address": ip_address or "unknown",
        "detail": detail or {}
    }
    
    # 1. Log to structured file/stdout (picked up by agent/collector)
    audit_logger.info(f"AUDIT_EVENT: {event}")
    
    # 2. Write to Firestore 'audit_logs' collection
    try:
        from firebase_admin import firestore
        db = firestore.client()
        # Use server timestamp for immutability
        event["server_timestamp"] = firestore.SERVER_TIMESTAMP
        db.collection('audit_logs').document().set(event)
    except Exception as e:
        audit_logger.error(f"Failed to write audit log to Firestore: {e}")
    
    return event
