from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class DataTransferLog(Base):
    """
    Law 2013-450 compliance: Log all cross-border data transfers.
    """
    __tablename__ = "data_transfer_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(128), nullable=False, index=True)
    transfer_type = Column(String(100), nullable=False) # e.g., 'payment_processing', 'whatsapp_message'
    destination_country = Column(String(2), nullable=False)
    destination_provider = Column(String(255), nullable=False)
    data_categories = Column(JSON, nullable=False) # e.g., ['financial', 'personal']
    legal_basis = Column(String(100), nullable=False)
    retention_until = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
