import aiohttp
import logging
import os
import uuid
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MTNMoMoCI:
    """
    MTN Mobile Money Open API Integration for Côte d'Ivoire.
    Uses Ocp-Apim-Subscription-Key and UUID references.
    """
    def __init__(self):
        self.base_url = os.getenv("MTN_MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com/disbursement/v1_0")
        self.subscription_key = os.getenv("MTN_MOMO_SUBSCRIPTION_KEY", "mock_mtn_sub_key")
        self.target_environment = os.getenv("MTN_MOMO_ENV", "sandbox")
        self.api_user = os.getenv("MTN_MOMO_API_USER", "mock_user")
        self.api_key = os.getenv("MTN_MOMO_API_KEY", "mock_key")

    async def _get_token(self) -> str:
        # In a real implementation this would fetch & cache a short-lived Bearer token
        return "mock_mtn_bearer_token"

    async def disburse(self, phone: str, amount: float, reference: str) -> Dict[str, Any]:
        bearer_token = await self._get_token()
        reference_id = str(uuid.uuid4()) # MTN requires a UUID for X-Reference-Id

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.target_environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": str(amount),
            "currency": "XOF",
            "externalId": reference,
            "payee": {
                "partyIdType": "MSISDN",
                "partyId": phone
            },
            "payerMessage": "Paiement Wali Assurance",
            "payeeNote": "Paiement Wali Assurance"
        }

        if self.subscription_key == "mock_mtn_sub_key":
            logger.info(f"Mocking MTN MoMo disbursement of {amount} to {phone}")
            return {"status": "success", "transaction_id": f"MTN_MOCK_{reference_id}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/transfer", json=payload, headers=headers, timeout=15) as response:
                    # MTN returns 202 Accepted usually for asynchronous completion
                    if response.status in (200, 201, 202):
                        return {"status": "success", "transaction_id": reference_id}
                    else:
                        error_text = await response.text()
                        logger.error(f"MTN MoMo API Error: {response.status} - {error_text}")
                        return {"status": "failed", "error": error_text}
        except Exception as e:
            logger.exception("MTN MoMo Connection Error")
            return {"status": "failed", "error": str(e)}
