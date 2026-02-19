"""Rate limiting configuration for Compliance Service."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Use memory storage (no external dependency)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["100/minute"]
)
