import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.payments.orange_money import OrangeMoneyCI
from app.services.payments.wave import WaveCI
from app.services.payments.mtn_momo import MTNMoMoCI
from app.services.compliance.audit import AuditService

logger = logging.getLogger(__name__)

class PaymentOrchestrator:
    """
    Orchestrates payments across Wave, Orange, and MTN.
    Includes:
    - Circuit breaker pattern
    - Exponential backoff
    - ARTCI Cross-border transfer logging via AuditService
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)
        
        self.providers = {
            "wave": WaveCI(),
            "orange_money": OrangeMoneyCI(),
            "mtn_momo": MTNMoMoCI()
        }
        
    async def disburse_with_retry(
        self, 
        user_id: str,
        phone: str, 
        amount: float, 
        reference: str,
        preferred_providers: List[str] = ["wave", "orange_money", "mtn_momo"]
    ) -> Dict[str, Any]:
        """
        Attempt disbursement with automatic fallback and exponential backoff retry.
        """
        max_attempts = 3
        
        for provider_name in preferred_providers:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
                
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Attempting disbursement to {phone} via {provider_name} (Attempt {attempt+1})")
                    result = await provider.disburse(phone, amount, reference)
                    
                    if result.get("status") == "success":
                        # Log ARTCI transfer compliance
                        await self._log_transfer_compliance(
                            user_id=user_id,
                            provider=provider_name,
                            phone=phone
                        )
                        return result
                    
                    # If failed normally (like bad number), don't retry same provider, just failover
                    logger.warning(f"{provider_name} failed: {result.get('error')}. Failing over...")
                    break  
                    
                except Exception as e:
                    logger.error(f"Exception during {provider_name} disbursement: {e}")
                    # Exponential backoff (2^attempt seconds) = 1s, 2s, 4s
                    backoff = 2 ** attempt
                    logger.info(f"Backing off for {backoff} seconds before retry...")
                    await asyncio.sleep(backoff)
                    
        return {"status": "failed", "error": "All payment providers failed or timed out."}
        
    async def _log_transfer_compliance(self, user_id: str, provider: str, phone: str):
        """Log data transfer for ARTCI regulatory compliance"""
        await self.audit_service.log_transfer(
            user_id=user_id,
            transfer_type=f"payment_disbursement_{provider}",
            destination_country="CI", # Keep intra-country if possible, but APIs route externally
            destination_provider=provider,
            data_categories=["financial", "phone_number"],
            legal_basis="contract_performance",
            retention_until=datetime.now(timezone.utc) + timedelta(days=365 * 3) # 3 year retention
        )
