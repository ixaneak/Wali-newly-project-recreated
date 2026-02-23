import hmac
import hashlib
import base64

class AfricasTalkingProvider:
    """
    Provider implementation for Africa's Talking USSD Gateway.
    Handles parsing, formatting, and security verification.
    """
    def __init__(self, api_key: str, username: str):
        self.api_key = api_key
        self.username = username

    def parse_request(self, form_data: dict) -> dict:
        """Parse incoming form data from Africa's Talking."""
        return {
            "session_id": form_data.get("sessionId", ""),
            "phone_number": self._normalize_phone(form_data.get("phoneNumber", "")),
            "network_code": form_data.get("networkCode", ""),
            "text": form_data.get("text", "")
        }

    def format_response(self, text: str, is_end: bool = False) -> str:
        """
        Format response for Africa's Talking.
        Prefixes with CON to continue, END to terminate the session.
        """
        prefix = "END " if is_end else "CON "
        return f"{prefix}{text.strip()}"

    def verify_callback(self, payload: str, signature: str) -> bool:
        """
        Verify the HMAC-SHA256 signature from Africa's Talking callback.
        """
        if not self.api_key or not signature:
            return False
            
        expected_signature = base64.b64encode(
            hmac.new(
                self.api_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(expected_signature, signature)

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone numbers to the standard Ivorian format: +225...
        """
        phone = phone.replace(" ", "").replace("-", "")
        
        if phone.startswith("+225"):
            if len(phone) == 14: # +225 07 XX XX XX XX
                return phone
            # if old 8 digit format, could try to adapt, but currently assuming new format
            return phone
        elif phone.startswith("225") and len(phone) == 13:
            return f"+{phone}"
        elif len(phone) == 10 and phone.startswith(("01", "05", "07")):
            return f"+225{phone}"
        
        return phone # return as is if no common pattern matches
