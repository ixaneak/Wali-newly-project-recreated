import os
import re
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

logger = logging.getLogger(__name__)

# Regex for detecting Ivorian and international phone numbers
PHONE_REGEX = re.compile(r'(\+225|00225)?\s*[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}')

def strip_pii_from_event(event, hint):
    """
    Sentry before_send hook.
    ARTCI/GDPR Compliance: Scrub PII (Phone numbers, emails, passwords) before sending to Sentry.
    """
    def scrub_data(data):
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    # Mask phone numbers
                    data[k] = PHONE_REGEX.sub("[REDACTED_PHONE]", v)
                    
                    # Mask emails
                    if "@" in v and "." in v:
                        parts = v.split("@")
                        if len(parts) == 2:
                            domain = parts[1]
                            data[k] = f"[REDACTED_EMAIL]@{domain}"
                
                # Check keys for sensitive terms
                elif k.lower() in ("password", "secret", "token", "api_key", "authorization"):
                    data[k] = "[REDACTED_SECRET]"
                    
                else:
                    scrub_data(v)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str):
                    data[i] = PHONE_REGEX.sub("[REDACTED_PHONE]", item)
                else:
                    scrub_data(item)
    
    # Scrub the entire event payload
    try:
        scrub_data(event)
    except Exception as e:
        logger.error(f"Error scrubbing Sentry event: {e}")
        return None # Drop the event if we can't guarantee PII safety

    return event

def init_sentry():
    """Initialize Sentry SDK with integrations and PII scrubbing."""
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("ENVIRONMENT", "development")
    
    if not sentry_dsn:
        logger.warning("SENTRY_DSN not found. Error tracking disabled.")
        return
        
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        traces_sample_rate=0.2 if environment == "production" else 1.0,
        profiles_sample_rate=0.2 if environment == "production" else 1.0,
        before_send=strip_pii_from_event,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration()
        ],
    )
    logger.info("Sentry initialized with ARTCI PII scrubbing.")
