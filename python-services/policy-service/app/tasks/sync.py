import logging
from typing import Dict, Any

from celery import shared_task
from app.core.celery_app import celery_app

try:
    from firebase_admin import auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)

@celery_app.task(
    name="app.tasks.sync.sync_user_to_firebase",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def sync_user_to_firebase(self, internal_user_id: str, phone: str, custom_claims: Dict[str, Any] = None):
    """
    Sync internal user state to Firebase Auth outbox (e.g. role updates, ban status).
    Uses exponential backoff on failure.
    """
    if not FIREBASE_AVAILABLE:
        logger.warning(f"Firebase not available. Skipping sync for user: {internal_user_id}")
        return {"status": "skipped", "reason": "firebase_not_configured"}
        
    try:
        logger.info(f"Syncing user {internal_user_id} ({phone}) to Firebase")
        
        # 1. Lookup Firebase user by phone number
        try:
            firebase_user = auth.get_user_by_phone_number(phone)
        except auth.UserNotFoundError:
            # Create user if they don't exist yet but were onboarded via USSD/WhatsApp
            logger.info(f"User {phone} not found in Firebase. Creating shell account.")
            firebase_user = auth.create_user(
                uid=internal_user_id,
                phone_number=phone,
                disabled=False
            )
            
        # 2. Update custom claims (Role, Tier, etc.)
        if custom_claims:
            current_claims = firebase_user.custom_claims or {}
            current_claims.update(custom_claims)
            auth.set_custom_user_claims(firebase_user.uid, current_claims)
            
        return {"status": "success", "firebase_uid": firebase_user.uid}
        
    except Exception as exc:
        logger.error(f"Error syncing user to Firebase: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)
