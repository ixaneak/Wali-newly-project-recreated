"""
WhatsApp Webhook Handler.

Processes incoming webhooks from Meta:
- Message reception
- Delivery status updates
- Interactive message responses
- Media (images) for claims

Security:
- HMAC-SHA256 signature verification
- Rate limiting
- Fraud detection on images
"""
import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from uuid import uuid4

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.whatsapp.models import (
    WhatsAppWebhookPayload,
    IncomingMessage,
    MessageDirection,
    MessageType,
    MessageStatus,
    WhatsAppMessageLog,
    WhatsAppConversation,
    ConversationState,
    WhatsAppMediaLog,
    LanguageCode
)
from app.whatsapp.state_machine import StateMachine, StateTransitionError
from app.whatsapp.client import WhatsAppClient
from app.whatsapp.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])

# Global state machine instance
state_machine: Optional[StateMachine] = None
whatsapp_client: Optional[WhatsAppClient] = None
image_processor: Optional[ImageProcessor] = None


def init_webhook_handler(
    sm: StateMachine,
    client: WhatsAppClient,
    img_processor: ImageProcessor
):
    """Initialize webhook handler with dependencies."""
    global state_machine, whatsapp_client, image_processor
    state_machine = sm
    whatsapp_client = client
    image_processor = img_processor


@router.get("")
async def verify_webhook(
    request: Request,
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """
    Webhook verification endpoint.
    Meta sends GET request to verify endpoint.
    """
    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    if not whatsapp_client:
        raise HTTPException(status_code=500, detail="Webhook handler not initialized")
    
    if not whatsapp_client.verify_webhook_token(hub_verify_token or ""):
        raise HTTPException(status_code=403, detail="Invalid verify token")
    
    logger.info("Webhook verified successfully")
    return Response(content=hub_challenge, media_type="text/plain")


@router.post("")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive and process incoming webhooks from Meta.
    
    Security:
    - Signature verification
    - Idempotency check
    - Rate limiting
    """
    if not all([state_machine, whatsapp_client]):
        raise HTTPException(status_code=500, detail="Webhook handler not initialized")
    
    # Read raw body for signature verification
    body = await request.body()
    
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not whatsapp_client.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse payload
    try:
        data = await request.json()
        payload = WhatsAppWebhookPayload(**data)
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    # Process each entry
    for entry in payload.entry:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            
            # Process messages
            if "messages" in value:
                for message in value["messages"]:
                    await _process_inbound_message(message, db)
            
            # Process status updates
            if "statuses" in value:
                for status in value["statuses"]:
                    await _process_status_update(status, db)
    
    return Response(status_code=200)


async def _process_inbound_message(
    message_data: Dict[str, Any],
    db: Session
):
    """Process an inbound message from WhatsApp."""
    try:
        # Parse message
        message = _parse_message(message_data)
        
        # Get or create conversation
        conversation = _get_or_create_conversation(message.phone, db)
        
        # Check rate limiting
        if not conversation.can_send_message():
            logger.warning(f"Rate limit exceeded for {message.phone}")
            return
        
        # Increment message count
        conversation.message_count += 1
        
        # Check for duplicate message (idempotency)
        existing = db.query(WhatsAppMessageLog).filter(
            WhatsAppMessageLog.message_id == message.message_id
        ).first()
        
        if existing:
            logger.debug(f"Duplicate message {message.message_id} ignored")
            return
        
        # Log the message
        log = WhatsAppMessageLog(
            message_id=message.message_id,
            phone=message.phone,
            conversation_id=conversation.id,
            direction=MessageDirection.INBOUND,
            message_type=_get_message_type(message.type),
            content_hash=_hash_content(message.text or ""),
            content_preview=message.text[:200] if message.text else None,
            status=MessageStatus.DELIVERED,
            idempotency_key=str(uuid4()),
            timestamp=message.timestamp
        )
        db.add(log)
        
        # Process based on message type
        if message.type == "text":
            await _process_text_message(conversation, message, db)
        elif message.type == "image":
            await _process_image_message(conversation, message, db)
        elif message.type == "interactive":
            await _process_interactive_message(conversation, message, db)
        elif message.type == "location":
            await _process_location_message(conversation, message, db)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error processing inbound message: {e}")
        db.rollback()


def _parse_message(data: Dict[str, Any]) -> IncomingMessage:
    """Parse raw message data from Meta."""
    message_id = data.get("id")
    phone = data.get("from")
    timestamp = datetime.fromtimestamp(int(data.get("timestamp", 0)))
    
    # Determine message type
    msg_type = "text"
    text = None
    image_id = None
    location = None
    button_reply = None
    list_reply = None
    
    if "text" in data:
        msg_type = "text"
        text = data["text"].get("body", "")
    elif "image" in data:
        msg_type = "image"
        image_id = data["image"].get("id")
    elif "location" in data:
        msg_type = "location"
        location = {
            "latitude": data["location"].get("latitude"),
            "longitude": data["location"].get("longitude"),
            "name": data["location"].get("name")
        }
    elif "interactive" in data:
        msg_type = "interactive"
        interactive = data["interactive"]
        if "button_reply" in interactive:
            button_reply = interactive["button_reply"].get("id")
        elif "list_reply" in interactive:
            list_reply = interactive["list_reply"].get("id")
    
    return IncomingMessage(
        message_id=message_id,
        phone=phone,
        timestamp=timestamp,
        type=msg_type,
        text=text,
        image_id=image_id,
        location=location,
        button_reply=button_reply,
        list_reply=list_reply
    )


def _get_or_create_conversation(
    phone: str,
    db: Session
) -> WhatsAppConversation:
    """Get existing conversation or create new one."""
    conversation = db.query(WhatsAppConversation).filter(
        WhatsAppConversation.phone == phone
    ).first()
    
    if not conversation:
        conversation = WhatsAppConversation(
            phone=phone,
            state=ConversationState.OPT_IN_REQUIRED,
            opted_in=False
        )
        db.add(conversation)
        db.flush()
        logger.info(f"New conversation created for {phone}")
    
    return conversation


def _get_message_type(type_str: str) -> MessageType:
    """Map string type to MessageType enum."""
    type_map = {
        "text": MessageType.TEXT,
        "image": MessageType.IMAGE,
        "document": MessageType.DOCUMENT,
        "interactive": MessageType.INTERACTIVE,
        "location": MessageType.LOCATION,
    }
    return type_map.get(type_str, MessageType.TEXT)


def _hash_content(content: str) -> str:
    """Generate SHA-256 hash of content."""
    import hashlib
    return hashlib.sha256(content.encode()).hexdigest()


async def _process_text_message(
    conversation: WhatsAppConversation,
    message: IncomingMessage,
    db: Session
):
    """Process text message based on current state."""
    text = message.text.lower().strip() if message.text else ""
    
    # Handle opt-in
    if conversation.state == ConversationState.OPT_IN_REQUIRED:
        if text in ["ok", "oui", "yes", "accord"]:
            conversation.opted_in = True
            conversation.opted_in_at = datetime.utcnow()
            state_machine.transition(
                conversation,
                ConversationState.IDLE,
                message_id=message.message_id
            )
            await _send_welcome_message(conversation)
        return
    
    # Handle group enrollment command
    if text.startswith("groupe ") or text.startswith("group "):
        await _handle_group_enrollment_command(conversation, text, db)
        return
    
    # Handle other commands based on state
    # This would be expanded based on business logic
    if text in ["claim", "sinistre", "reclamation"]:
        state_machine.transition(
            conversation,
            ConversationState.ACTIVE_CLAIM,
            message_id=message.message_id
        )
        await _send_claim_start_message(conversation)
    elif text in ["help", "aide", "support"]:
        await _send_support_message(conversation)
    else:
        # Default: send menu
        await _send_main_menu(conversation)


async def _process_image_message(
    conversation: WhatsAppConversation,
    message: IncomingMessage,
    db: Session
):
    """Process image message (claims documentation)."""
    if conversation.state not in [
        ConversationState.ACTIVE_CLAIM,
        ConversationState.DOCUMENT_UPLOAD
    ]:
        # Not expecting images
        conversation.invalid_image_count += 1
        if conversation.invalid_image_count >= 5:
            # Auto-block user
            conversation.blocked_until = datetime.utcnow() + timedelta(hours=24)
        return
    
    # Download and process image
    if message.image_id and image_processor:
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp_path = tmp.name
            
            # Download from Meta
            downloaded_path = whatsapp_client.download_media(
                message.image_id,
                tmp_path
            )
            
            # Process image (fraud detection, compression, encryption)
            result = await image_processor.process_claim_image(
                downloaded_path,
                conversation,
                db
            )
            
            # Update conversation state
            if result.get("is_valid"):
                state_machine.transition(
                    conversation,
                    ConversationState.FRAUD_REVIEW,
                    context_update={"image_processed": True},
                    message_id=message.message_id
                )
                await _send_image_received_confirmation(conversation)
            else:
                conversation.invalid_image_count += 1
                await _send_image_rejection(conversation, result.get("errors", []))
            
            # Cleanup temp file
            os.unlink(downloaded_path)
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            await _send_image_error_message(conversation)


async def _process_interactive_message(
    conversation: WhatsAppConversation,
    message: IncomingMessage,
    db: Session
):
    """Process interactive message (button/list replies)."""
    reply = message.button_reply or message.list_reply
    if not reply:
        return
    
    # Parse reply ID format: "action:value"
    parts = reply.split(":", 1)
    action = parts[0]
    value = parts[1] if len(parts) > 1 else None
    
    if action == "trade":
        state_machine.transition(
            conversation,
            ConversationState.TRADE_SELECTION,
            context_update={"trade": value},
            message_id=message.message_id
        )
        await _send_plan_selection_menu(conversation)
    
    elif action == "plan":
        context_update = {"plan_type": value}
        
        if value == "family":
            # Must go through PARENT_CONFIRMATION for family plans (CIMA)
            state_machine.transition(
                conversation,
                ConversationState.PARENT_CONFIRMATION,
                context_update=context_update,
                message_id=message.message_id
            )
            await _send_parent_confirmation_request(conversation)
        else:
            state_machine.transition(
                conversation,
                ConversationState.LOCATION_CAPTURE,
                context_update=context_update,
                message_id=message.message_id
            )
            await _send_location_request(conversation)
    
    elif action == "parents_confirm":
        if value == "yes":
            state_machine.transition(
                conversation,
                conversation.context.get("next_state", ConversationState.LOCATION_CAPTURE),
                context_update={"parents_confirmed": True, "covers_parents": True},
                message_id=message.message_id
            )
            await _send_location_request(conversation)
        else:
            await _send_parent_opt_out_message(conversation)


async def _process_location_message(
    conversation: WhatsAppConversation,
    message: IncomingMessage,
    db: Session
):
    """Process location message."""
    if conversation.state == ConversationState.LOCATION_CAPTURE:
        if message.location:
            lat = message.location.get("latitude")
            lng = message.location.get("longitude")
            
            # Validate Ivory Coast bounds
            if lat and lng and 4.0 <= lat <= 11.0 and -8.0 <= lng <= -3.0:
                state_machine.transition(
                    conversation,
                    ConversationState.PAYMENT_PENDING,
                    context_update={
                        "latitude": lat,
                        "longitude": lng,
                        "location_name": message.location.get("name")
                    },
                    message_id=message.message_id
                )
                await _send_payment_instructions(conversation)
            else:
                await _send_invalid_location_message(conversation)


async def _process_status_update(
    status_data: Dict[str, Any],
    db: Session
):
    """Process message status update."""
    message_id = status_data.get("id")
    status = status_data.get("status")  # sent, delivered, read, failed
    
    # Update message log
    log = db.query(WhatsAppMessageLog).filter(
        WhatsAppMessageLog.message_id == message_id
    ).first()
    
    if log:
        status_map = {
            "sent": MessageStatus.SENT,
            "delivered": MessageStatus.DELIVERED,
            "read": MessageStatus.READ,
            "failed": MessageStatus.FAILED,
        }
        log.status = status_map.get(status, MessageStatus.PENDING)
        log.status_updated_at = datetime.utcnow()
        
        if status == "failed":
            log.error_code = status_data.get("errors", [{}])[0].get("code")
            log.error_message = status_data.get("errors", [{}])[0].get("message")
        
        db.commit()


# Response message helpers
async def _send_welcome_message(conversation: WhatsAppConversation):
    """Send welcome message."""
    if not whatsapp_client:
        return
    
    try:
        whatsapp_client.send_template_message(
            phone=conversation.phone,
            template_name="welcome_message",
            language=conversation.language.value,
            params=["Wali", "+225 07 07 07 07 07"]
        )
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")


async def _send_main_menu(conversation: WhatsAppConversation):
    """Send main menu with interactive buttons."""
    # Implementation would use interactive messages
    pass


async def _send_claim_start_message(conversation: WhatsAppConversation):
    """Send claim initiation message."""
    pass


async def _send_support_message(conversation: WhatsAppConversation):
    """Send support contact information."""
    pass


async def _handle_group_enrollment_command(
    conversation: WhatsAppConversation,
    text: str,
    db: Session
):
    """Handle group enrollment command."""
    # Parse: "GROUPE [name] [count]"
    pass


async def _send_plan_selection_menu(conversation: WhatsAppConversation):
    """Send plan selection interactive message."""
    pass


async def _send_parent_confirmation_request(conversation: WhatsAppConversation):
    """Send parent coverage confirmation request (CIMA requirement)."""
    pass


async def _send_parent_opt_out_message(conversation: WhatsAppConversation):
    """Send message when parent coverage declined."""
    pass


async def _send_location_request(conversation: WhatsAppConversation):
    """Send location request message."""
    pass


async def _send_invalid_location_message(conversation: WhatsAppConversation):
    """Send invalid location error."""
    pass


async def _send_payment_instructions(conversation: WhatsAppConversation):
    """Send payment instructions."""
    pass


async def _send_image_received_confirmation(conversation: WhatsAppConversation):
    """Send confirmation that image was received."""
    pass


async def _send_image_rejection(conversation: WhatsAppConversation, errors: list):
    """Send image rejection message with reasons."""
    pass


async def _send_image_error_message(conversation: WhatsAppConversation):
    """Send error message for image processing failure."""
    pass
