from sqlalchemy import Column, String, DateTime, Enum, JSON, Boolean
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class DocumentType(str, enum.Enum):
    PRIVACY_POLICY = "privacy-policy"
    TERMS_OF_SERVICE = "terms-of-service"
    PHARMACY_AGREEMENT = "pharmacy-agreement"

class LegalConfig(Base):
    __tablename__ = "legal_configs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rccm = Column(String(100), nullable=False)
    cc = Column(String(100), nullable=False)
    email_dpo = Column(String(255), nullable=False)
    artci_authorization = Column(String(255), nullable=False)
    support_phone = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class LegalTemplate(Base):
    __tablename__ = "legal_templates"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_type = Column(Enum(DocumentType), unique=True, nullable=False, index=True)
    content = Column(String, nullable=False)  # Markdown or HTML content with {{ place_holders }}
    version = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
