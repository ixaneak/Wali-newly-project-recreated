import aiohttp
import logging
import os
import hashlib
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WaveCI:
    """
    Wave Mobile Money CI Integration.
    Requires strict Idempotency-Key handling.
    """
    def __init__(self):
        self.base_url = os.getenv("WAVE_BASE_URL", "https://api.wave.com/v1")
        self.api_key = os.getenv("WAVE_API_KEY", "mock_wave_api_key")

    def _generate_idempotency_key(self, reference: str) -> str:
        return hashlib.sha256(reference.encode()).hexdigest()

    async def disburse(self, phone: str, amount: float, reference: str) -> Dict[str, Any]:
        idem_key = self._generate_idempotency_key(reference)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": idem_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": str(amount),
            "currency": "XOF",
            "mobile": phone,
            "client_reference": reference
        }

        if self.api_key == "mock_wave_api_key":
            logger.info(f"Mocking Wave disbursement of {amount} to {phone}")
            return {"status": "success", "transaction_id": f"WAVE_MOCK_{reference}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/payouts", json=payload, headers=headers, timeout=15) as response:
                    if response.status in (200, 201):
                        data = await response.json()
                        return {"status": "success", "transaction_id": data.get("id")}
                    else:
                        error_text = await response.text()
                        logger.error(f"Wave API Error: {response.status} - {error_text}")
                        return {"status": "failed", "error": error_text}
        except Exception as e:
            logger.exception("Wave Connection Error")
            return {"status": "failed", "error": str(e)}
