from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import get_settings
import os

# Use memory instead of Redis (no external dependency)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["100/minute"]
)
