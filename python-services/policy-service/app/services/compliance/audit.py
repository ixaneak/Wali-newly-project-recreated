from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.models.compliance import DataTransferLog

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_transfer(
        self,
        user_id: str,
        transfer_type: str,
        destination_country: str,
        destination_provider: str,
        data_categories: list[str],
        legal_basis: str,
        retention_until: datetime
    ) -> DataTransferLog:
        """
        Log cross-border data transfer for ARTCI compliance.
        Must be called for all external API transfers (Meta, SMS providers, Payment Gateways).
        """
        log_entry = DataTransferLog(
            user_id=user_id,
            transfer_type=transfer_type,
            destination_country=destination_country,
            destination_provider=destination_provider,
            data_categories=data_categories,
            legal_basis=legal_basis,
            retention_until=retention_until
        )
        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)
        return log_entry
