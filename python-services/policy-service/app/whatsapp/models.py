"""
WhatsApp Business API Models for Wali Assurance.

CIMA-compliant models for WhatsApp conversations, message logging,
and B2B group enrollments.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, Dict, Any, List
from uuid import uuid4, UUID

from sqlalchemy import (
    Column, String, DateTime, Integer, Boolean, ForeignKey, 
    Text, Numeric, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class ConversationState(str, PyEnum):
    """Finite state machine states for WhatsApp conversations."""
    OPT_IN_REQUIRED = "OPT_IN_REQUIRED"
    IDLE = "IDLE"
    B2B_ENROLLMENT = "B2B_ENROLLMENT"
    TRADE_SELECTION = "TRADE_SELECTION"
    PLAN_SELECTION = "PLAN_SELECTION"
    PARENT_CONFIRMATION = "PARENT_CONFIRMATION"
    LOCATION_CAPTURE = "LOCATION_CAPTURE"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    ACTIVE_CLAIM = "ACTIVE_CLAIM"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    FRAUD_REVIEW = "FRAUD_REVIEW"
    SETTLEMENT = "SETTLEMENT"
    SUPPORT = "SUPPORT"


class MessageDirection(str, PyEnum):
    """Message direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageType(str, PyEnum):
    """WhatsApp message types."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"
    LOCATION = "location"


class MessageStatus(str, PyEnum):
    """Message delivery status."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"


class GroupEnrollmentStatus(str, PyEnum):
    """Group enrollment status."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LanguageCode(str, PyEnum):
    """Supported languages."""
    FRENCH = "fr"
    DIOULA = "dy"
    BAOULE = "ba"


class WhatsAppConversation(Base):
    """
    Tracks the state and context of a WhatsApp conversation.
    
    CIMA Compliance:
    - All conversations logged with timestamp
    - Opt-in required before processing (GDPR/Law 2013-450)
    - 3-year retention with auto-purge
    """
    __tablename__ = "whatsapp_conversations"
    __table_args__ = (
        Index("ix_conversations_phone", "phone"),
        Index("ix_conversations_state", "state"),
        Index("ix_conversations_group_id", "group_id"),
        Index("ix_conversations_last_interaction", "last_interaction"),
        {"comment": "WhatsApp conversation state tracking"},
    )

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    phone: str = Column(String(20), nullable=False, unique=True, index=True)
    
    # State machine
    state: ConversationState = Column(
        Enum(ConversationState), 
        nullable=False, 
        default=ConversationState.OPT_IN_REQUIRED
    )
    context: Dict[str, Any] = Column(JSONB, default=dict)
    
    # Metadata
    last_interaction: datetime = Column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        onupdate=func.now()
    )
    message_count: int = Column(Integer, default=0)
    message_count_window: datetime = Column(DateTime(timezone=True))  # For rate limiting
    
    # Compliance
    opted_in: bool = Column(Boolean, default=False)
    opted_in_at: Optional[datetime] = Column(DateTime(timezone=True))
    language: LanguageCode = Column(Enum(LanguageCode), default=LanguageCode.FRENCH)
    
    # B2B Group enrollment
    group_id: Optional[UUID] = Column(PGUUID(as_uuid=True), ForeignKey("group_enrollments.id"))
    
    # Fraud prevention
    invalid_image_count: int = Column(Integer, default=0)
    blocked_until: Optional[datetime] = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    group = relationship("GroupEnrollment", back_populates="members")
    messages = relationship("WhatsAppMessageLog", back_populates="conversation", lazy="dynamic")

    def is_blocked(self) -> bool:
        """Check if user is currently blocked."""
        if self.blocked_until and self.blocked_until > datetime.utcnow():
            return True
        return False

    def can_send_message(self) -> bool:
        """Check if user can send messages (rate limiting)."""
        if self.is_blocked():
            return False
        
        # Reset counter if window expired (1 minute)
        if self.message_count_window:
            if (datetime.utcnow() - self.message_count_window).total_seconds() > 60:
                self.message_count = 0
                self.message_count_window = datetime.utcnow()
        else:
            self.message_count_window = datetime.utcnow()
        
        # Max 30 messages per minute
        return self.message_count < 30


class WhatsAppMessageLog(Base):
    """
    Audit trail for all WhatsApp messages.
    
    CIMA Compliance:
    - Every message stored with hash
    - Immutable audit trail
    - 3-year retention
    """
    __tablename__ = "whatsapp_message_logs"
    __table_args__ = (
        Index("ix_message_logs_conversation_id", "conversation_id"),
        Index("ix_message_logs_message_id", "message_id"),
        Index("ix_message_logs_timestamp", "timestamp"),
        Index("ix_message_logs_phone", "phone"),
        {"comment": "WhatsApp message audit trail"},
    )

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Message identifiers
    message_id: str = Column(String(100), nullable=False, index=True)  # Meta's wamid.xxx
    phone: str = Column(String(20), nullable=False, index=True)
    conversation_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("whatsapp_conversations.id"), nullable=False)
    
    # Message content
    direction: MessageDirection = Column(Enum(MessageDirection), nullable=False)
    message_type: MessageType = Column(Enum(MessageType), nullable=False)
    content_hash: str = Column(String(64), nullable=False)  # SHA-256
    content_preview: Optional[str] = Column(Text)  # Truncated for audit
    
    # Template info
    template_name: Optional[str] = Column(String(100))
    template_language: Optional[str] = Column(String(10))
    
    # Status tracking
    status: MessageStatus = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
    status_updated_at: Optional[datetime] = Column(DateTime(timezone=True))
    
    # Idempotency
    idempotency_key: str = Column(String(36), unique=True, nullable=False)
    
    # Error tracking
    error_code: Optional[str] = Column(String(50))
    error_message: Optional[str] = Column(Text)
    
    # Cross-border transfer log (Law 2013-450)
    transferred_to: str = Column(String(50), default="Meta-WhatsApp-US")
    transfer_logged: bool = Column(Boolean, default=False)
    
    # Timestamps
    timestamp: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    conversation = relationship("WhatsAppConversation", back_populates="messages")


class GroupEnrollment(Base):
    """
    B2B Group enrollment (syndicates/cooperatives).
    
    CIMA Requirements:
    - Max 100 members per group
    - Minimum 5 members for group rate
    - Same region for all members
    """
    __tablename__ = "group_enrollments"
    __table_args__ = (
        Index("ix_group_enrollments_code", "code", unique=True),
        Index("ix_group_enrollments_leader_phone", "leader_phone"),
        Index("ix_group_enrollments_status", "status"),
        {"comment": "B2B group enrollment tracking"},
    )

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: str = Column(String(10), nullable=False, unique=True, index=True)
    
    # Group info
    name: str = Column(String(200), nullable=False)
    leader_phone: str = Column(String(20), nullable=False, index=True)
    leader_name: Optional[str] = Column(String(200))
    
    # Region constraint
    region: str = Column(String(100), nullable=False)
    
    # Member tracking
    member_count: int = Column(Integer, default=0)
    max_members: int = Column(Integer, default=100)  # CIMA limit
    min_members: int = Column(Integer, default=5)    # For group rate
    
    # Pricing
    base_premium_per_member: Decimal = Column(Numeric(10, 2), nullable=False)
    discount_rate: Decimal = Column(Numeric(3, 2), default=Decimal("0.10"))  # 10%
    total_collected: Decimal = Column(Numeric(12, 2), default=Decimal("0.00"))
    
    # Commission
    commission_rate: Decimal = Column(Numeric(3, 2), default=Decimal("0.05"))  # 5%
    commission_paid: Decimal = Column(Numeric(12, 2), default=Decimal("0.00"))
    
    # Status
    status: GroupEnrollmentStatus = Column(
        Enum(GroupEnrollmentStatus), 
        default=GroupEnrollmentStatus.PENDING
    )
    
    # Timestamps
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    completed_at: Optional[datetime] = Column(DateTime(timezone=True))
    
    # Relationships
    members = relationship("WhatsAppConversation", back_populates="group")
    
    def calculate_discount(self) -> Decimal:
        """Calculate discount based on member count."""
        if self.member_count >= self.min_members:
            return self.base_premium_per_member * self.discount_rate
        return Decimal("0.00")
    
    def calculate_commission(self) -> Decimal:
        """Calculate leader commission."""
        return self.total_collected * self.commission_rate
    
    def can_add_member(self) -> bool:
        """Check if more members can be added."""
        return self.member_count < self.max_members and self.status in [
            GroupEnrollmentStatus.PENDING, 
            GroupEnrollmentStatus.ACTIVE
        ]


class WhatsAppMediaLog(Base):
    """
    Media (images) sent via WhatsApp for claims.
    
    Fraud Detection:
    - Perceptual hash comparison
    - EXIF analysis
    - GPS validation
    """
    __tablename__ = "whatsapp_media_logs"
    __table_args__ = (
        Index("ix_media_logs_conversation_id", "conversation_id"),
        Index("ix_media_logs_perceptual_hash", "perceptual_hash"),
        Index("ix_media_logs_created_at", "created_at"),
        {"comment": "WhatsApp media (claims) with fraud detection"},
    )

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Links
    conversation_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("whatsapp_conversations.id"), nullable=False)
    message_id: str = Column(String(100), nullable=False, index=True)
    
    # Media info
    media_id: str = Column(String(200), nullable=False)  # Meta's media ID
    mime_type: str = Column(String(50), nullable=False)
    file_size: int = Column(Integer)  # bytes
    
    # Storage
    s3_bucket: str = Column(String(100), nullable=False)
    s3_key: str = Column(String(500), nullable=False)
    
    # Fraud detection
    perceptual_hash: Optional[str] = Column(String(64), index=True)
    content_hash: str = Column(String(64), nullable=False)  # SHA-256
    exif_data: Optional[Dict[str, Any]] = Column(JSONB)
    gps_latitude: Optional[Decimal] = Column(Numeric(10, 8))
    gps_longitude: Optional[Decimal] = Column(Numeric(11, 8))
    
    # Validation
    is_duplicate: bool = Column(Boolean, default=False)
    duplicate_of_id: Optional[UUID] = Column(PGUUID(as_uuid=True))
    is_valid: bool = Column(Boolean, default=True)
    validation_errors: List[str] = Column(JSONB, default=list)
    
    # Encryption
    encryption_key_id: str = Column(String(100), nullable=False)
    
    # Retention (auto-purge after 3 years)
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now())
    purge_after: datetime = Column(DateTime(timezone=True), nullable=False)


class CrossBorderTransferLog(Base):
    """
    Law 2013-450 compliance: Log all cross-border data transfers.
    
    Required for every Meta API call (destination: US).
    """
    __tablename__ = "cross_border_transfer_logs"
    __table_args__ = (
        Index("ix_transfer_logs_timestamp", "timestamp"),
        {"comment": "Cross-border data transfer compliance logging"},
    )

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Transfer details
    transfer_type: str = Column(String(50), nullable=False)  # 'message', 'media', 'webhook'
    destination_country: str = Column(String(2), default="US")  # ISO 3166-1 alpha-2
    destination_provider: str = Column(String(100), default="Meta Platforms Inc.")
    
    # Data classification
    data_subject_phone: str = Column(String(20), nullable=False)
    data_categories: List[str] = Column(JSONB, default=list)  # ['personal', 'health', 'financial']
    
    # Legal basis
    legal_basis: str = Column(String(50), default="contract_performance")  # GDPR Article 6
    
    # Timestamps
    timestamp: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Retention
    retention_years: int = Column(Integer, default=3)
    purge_after: datetime = Column(DateTime(timezone=True), nullable=False)


class CommissionPayment(Base):
    """
    Track commission payments to group leaders.
    """
    __tablename__ = "commission_payments"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    group_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("group_enrollments.id"), nullable=False)
    
    leader_phone: str = Column(String(20), nullable=False)
    amount: Decimal = Column(Numeric(12, 2), nullable=False)
    
    # Payment tracking
    payment_method: str = Column(String(20), nullable=False)  # 'orange_money', 'wave', 'mtn'
    transaction_reference: Optional[str] = Column(String(100))
    status: str = Column(String(20), default="pending")  # 'pending', 'completed', 'failed'
    
    paid_at: Optional[datetime] = Column(DateTime(timezone=True))
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, default=func.now())


# Pydantic models for API validation
from pydantic import BaseModel, Field, validator

class WhatsAppWebhookPayload(BaseModel):
    """Incoming webhook from Meta."""
    object: str
    entry: List[Dict[str, Any]]


class IncomingMessage(BaseModel):
    """Parsed incoming WhatsApp message."""
    message_id: str
    phone: str
    timestamp: datetime
    type: str  # 'text', 'image', 'interactive', etc.
    
    # Content (one of these will be populated)
    text: Optional[str] = None
    image_id: Optional[str] = None
    document_id: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    
    # Interactive message responses
    button_reply: Optional[str] = None
    list_reply: Optional[str] = None
    
    @validator('phone')
    def normalize_phone(cls, v: str) -> str:
        """Normalize to E.164 format."""
        v = v.strip().replace(" ", "").replace("-", "")
        if v.startswith("0"):
            v = "+225" + v[1:]
        if not v.startswith("+"):
            v = "+225" + v
        return v


class OutboundMessage(BaseModel):
    """Outbound message request."""
    phone: str
    type: MessageType = MessageType.TEXT
    
    # Content
    text: Optional[str] = None
    template_name: Optional[str] = None
    template_language: Optional[str] = "fr"
    template_params: Optional[List[Dict[str, str]]] = None
    
    # Media
    media_id: Optional[str] = None
    media_url: Optional[str] = None
    
    # Interactive
    interactive: Optional[Dict[str, Any]] = None
    
    # Idempotency
    idempotency_key: Optional[str] = None


class GroupEnrollmentRequest(BaseModel):
    """Request to create a group enrollment."""
    name: str = Field(..., min_length=3, max_length=200)
    leader_phone: str
    leader_name: Optional[str] = None
    region: str
    expected_members: int = Field(..., ge=5, le=100)
    
    @validator('leader_phone')
    def normalize_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if v.startswith("0"):
            v = "+225" + v[1:]
        if not v.startswith("+"):
            v = "+225" + v
        return v
