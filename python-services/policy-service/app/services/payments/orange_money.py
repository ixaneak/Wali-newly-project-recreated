import aiohttp
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OrangeMoneyCI:
    """
    Orange Money CI Integration.
    Uses X-Auth-Token for authentication.
    """
    def __init__(self):
        self.base_url = os.getenv("ORANGE_MONEY_BASE_URL", "https://api.orange.com/orange-money-webpay/dev/v1")
        self.auth_token = os.getenv("ORANGE_MONEY_AUTH_TOKEN", "mock_om_auth_token")
        self.merchant_key = os.getenv("ORANGE_MONEY_MERCHANT_KEY", "mock_merchant_key")

    async def disburse(self, phone: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Disburse funds to an artisan/pharmacy.
        returns: {"status": "success"|"failed", "transaction_id": "...", "error": "..."}
        """
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "X-Auth-Token": self.merchant_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "amount": amount,
            "currency": "XOF",
            "order_id": reference,
            "subscriber_msisdn": phone,
            "merchant_key": self.merchant_key
        }

        # Sandbox mocking if testing
        if self.auth_token == "mock_om_auth_token":
            logger.info(f"Mocking Orange Money disbursement of {amount} to {phone}")
            return {"status": "success", "transaction_id": f"OM_MOCK_{reference}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/pay", json=payload, headers=headers, timeout=15) as response:
                    if response.status in (200, 201):
                        data = await response.json()
                        return {"status": "success", "transaction_id": data.get("txnid")}
                    else:
                        error_text = await response.text()
                        logger.error(f"Orange Money API Error: {response.status} - {error_text}")
                        return {"status": "failed", "error": error_text}
        except Exception as e:
            logger.exception("Orange Money Connection Error")
            return {"status": "failed", "error": str(e)}
