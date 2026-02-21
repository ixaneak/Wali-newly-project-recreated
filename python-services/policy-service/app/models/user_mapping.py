from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class UserMapping(Base):
    """
    Mapping between external identity providers (Firebase) and internal SQL IDs.
    """
    __tablename__ = "user_mappings"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    internal_user_id = Column(String(128), nullable=False, index=True)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    provider = Column(String(50), default="firebase")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
