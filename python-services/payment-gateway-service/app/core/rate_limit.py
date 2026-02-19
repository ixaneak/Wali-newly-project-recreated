"""Rate limiting configuration for Payment Gateway Service."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Stricter rate limits for payment operations
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["50/minute"]  # Stricter for payments
)
