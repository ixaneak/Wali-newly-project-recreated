"""
WhatsApp Business API Integration for Wali Assurance.

This module provides:
- State machine for conversation management
- Meta WhatsApp API client
- Webhook handlers
- Image processing with fraud detection
- B2B group enrollment

Usage:
    from app.whatsapp import WhatsAppService
    
    service = WhatsAppService(
        phone_number_id="123456789",
        access_token="YOUR_TOKEN",
        app_secret="YOUR_SECRET"
    )
    
    # Send message
    await service.send_text_message("+2250701010101", "Bonjour!")
"""
from .models import (
    WhatsAppConversation,
    WhatsAppMessageLog,
    GroupEnrollment,
    WhatsAppMediaLog,
    CrossBorderTransferLog,
    ConversationState,
    MessageDirection,
    MessageType,
    MessageStatus,
    GroupEnrollmentStatus,
    LanguageCode,
    IncomingMessage,
    OutboundMessage,
    WhatsAppWebhookPayload,
)
from .state_machine import StateMachine, StateTransitionError, ContextValidator
from .client import WhatsAppClient, WhatsAppAPIError, CircuitBreakerOpen
from .image_processor import ImageProcessor, ImageValidationError

__all__ = [
    # Models
    "WhatsAppConversation",
    "WhatsAppMessageLog",
    "GroupEnrollment",
    "WhatsAppMediaLog",
    "CrossBorderTransferLog",
    "ConversationState",
    "MessageDirection",
    "MessageType",
    "MessageStatus",
    "GroupEnrollmentStatus",
    "LanguageCode",
    "IncomingMessage",
    "OutboundMessage",
    "WhatsAppWebhookPayload",
    # State Machine
    "StateMachine",
    "StateTransitionError",
    "ContextValidator",
    # Client
    "WhatsAppClient",
    "WhatsAppAPIError",
    "CircuitBreakerOpen",
    # Image Processing
    "ImageProcessor",
    "ImageValidationError",
]
