"""
PayDunya Payment Gateway Configuration — TEST MODE

Handles API credentials, endpoint URLs, and HMAC-SHA256 hash verification
for Instant Payment Notifications (IPN).

Security: All keys are loaded from environment variables with PAYDUNYA_ prefix.
"""
import hashlib
import hmac
from typing import Dict, Any

from pydantic_settings import BaseSettings


class PaydunyaSettings(BaseSettings):
    """PayDunya Configuration — TEST MODE.
    
    All fields are loaded from env vars prefixed with PAYDUNYA_.
    Example: PAYDUNYA_MASTER_KEY=xxx in .env
    """
    MASTER_KEY: str = "I8kW0zC4-XJ2m-7P9q-R5sT-3U6v8X1y2Z3a"
    PRIVATE_KEY: str = "test_private_xXxXxXxXxXxXxXxXxXxXx"
    PUBLIC_KEY: str = "test_public_xXxXxXxXxXxXxXxXxXxXx"
    TOKEN: str = "VotreTokenIci"
    MODE: str = "test"  # CRITICAL: Keep as 'test' until RCCM ready

    # PayDunya endpoints
    BASE_URL: str = "https://app.paydunya.com/sandbox-api/v1"  # Sandbox
    LIVE_URL: str = "https://app.paydunya.com/api/v1"          # Production (do NOT use yet)

    class Config:
        env_prefix = "PAYDUNYA_"
        env_file = ".env"
        extra = "ignore"

    @property
    def api_url(self) -> str:
        """Return the correct base URL based on mode."""
        return self.BASE_URL if self.MODE == "test" else self.LIVE_URL

    @property
    def headers(self) -> Dict[str, str]:
        """Return PayDunya API auth headers."""
        return {
            "PAYDUNYA-MASTER-KEY": self.MASTER_KEY,
            "PAYDUNYA-PRIVATE-KEY": self.PRIVATE_KEY,
            "PAYDUNYA-PUBLIC-KEY": self.PUBLIC_KEY,
            "Content-Type": "application/json",
        }


# Singleton instance
paydunya_config = PaydunyaSettings()


def verify_paydunya_hash(payload: Dict[str, Any], private_key: str) -> bool:
    """
    Verify PayDunya webhook signature (SHA-256).

    PayDunya computes: sha256(invoice_token + status + private_key)
    and includes the result in data.hash.

    Args:
        payload: The full JSON payload from PayDunya's IPN callback.
        private_key: Your PayDunya private key.

    Returns:
        True if the hash matches, False otherwise.
    """
    try:
        received_hash = payload.get("data", {}).get("hash", "")
        if not received_hash:
            return False

        invoice = payload.get("data", {}).get("invoice", {})
        invoice_token = invoice.get("token", "")
        status = invoice.get("status", "")

        expected_string = f"{invoice_token}{status}{private_key}"
        expected_hash = hashlib.sha256(expected_string.encode("utf-8")).hexdigest()

        return hmac.compare_digest(received_hash, expected_hash)
    except Exception:
        return False


# Test phone numbers reference (PayDunya sandbox)
TEST_NUMBERS = {
    "orange_money": {"number": "+225 77777777", "pin": "1234"},
    "mtn_momo":     {"number": "+225 55555555", "pin": "1234"},
    "wave":         {"number": "+225 99999999", "pin": "1234"},
    "moov":         {"number": "+225 66666666", "pin": "1234"},
}
