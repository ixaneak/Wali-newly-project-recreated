"""
Compliance List Model

Whitelist/blacklist/PEP/sanctions screening lists.
Used to screen artisans, beneficiaries, and third parties.
"""
from sqlalchemy import Column, String, DateTime, Text, CheckConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


class ListType(str, enum.Enum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    PEP = "pep"         # Politically Exposed Persons
    SANCTIONS = "sanctions"


class IdentifierType(str, enum.Enum):
    PHONE = "phone"
    NAME = "name"
    DEVICE_ID = "device_id"


class ComplianceListEntry(Base):
    __tablename__ = "compliance_lists"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    list_type = Column(String(20), nullable=False)
    identifier = Column(String(100), nullable=False)  # phone, name, or device ID
    identifier_type = Column(String(20), nullable=False)
    reason = Column(Text)
    added_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL = permanent

    __table_args__ = (
        CheckConstraint(
            "list_type IN ('whitelist', 'blacklist', 'pep', 'sanctions')",
            name="cl_valid_list_type",
        ),
        CheckConstraint(
            "identifier_type IN ('phone', 'name', 'device_id')",
            name="cl_valid_identifier_type",
        ),
        Index("idx_cl_identifier", "identifier"),
        Index("idx_cl_list_type", "list_type"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "list_type": self.list_type,
            "identifier": self.identifier,
            "identifier_type": self.identifier_type,
            "reason": self.reason,
            "added_by": self.added_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
