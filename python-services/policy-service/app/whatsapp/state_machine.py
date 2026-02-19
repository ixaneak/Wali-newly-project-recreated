"""
Finite State Machine for WhatsApp Conversations.

Implements CIMA-compliant conversation flow with:
- State transitions validation
- 24-hour auto-timeout (Redis TTL)
- Idempotency (same message_id cannot trigger change twice)
- Parent confirmation requirement (CIMA compliance)
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, Callable, List
from functools import wraps
import logging

from .models import ConversationState, WhatsAppConversation

logger = logging.getLogger(__name__)


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class StateTimeoutError(Exception):
    """Raised when conversation has timed out."""
    pass


class StateMachine:
    """
    Finite State Machine for WhatsApp conversation management.
    
    Rules:
    1. Never skip PARENT_CONFIRMATION if Family plan selected
    2. Auto-timeout after 24 hours
    3. Idempotency: Same message_id cannot trigger state change twice
    """
    
    # Valid state transitions
    TRANSITIONS: Dict[ConversationState, List[ConversationState]] = {
        ConversationState.OPT_IN_REQUIRED: [
            ConversationState.IDLE,
            ConversationState.B2B_ENROLLMENT,
        ],
        ConversationState.IDLE: [
            ConversationState.B2B_ENROLLMENT,
            ConversationState.TRADE_SELECTION,
            ConversationState.PLAN_SELECTION,
            ConversationState.ACTIVE_CLAIM,
            ConversationState.SUPPORT,
        ],
        ConversationState.B2B_ENROLLMENT: [
            ConversationState.IDLE,
            ConversationState.TRADE_SELECTION,
        ],
        ConversationState.TRADE_SELECTION: [
            ConversationState.IDLE,
            ConversationState.PLAN_SELECTION,
        ],
        ConversationState.PLAN_SELECTION: [
            ConversationState.IDLE,
            ConversationState.PARENT_CONFIRMATION,
            ConversationState.LOCATION_CAPTURE,
            ConversationState.PAYMENT_PENDING,
        ],
        # CRITICAL: PARENT_CONFIRMATION is mandatory for family plans
        ConversationState.PARENT_CONFIRMATION: [
            ConversationState.IDLE,
            ConversationState.LOCATION_CAPTURE,
            ConversationState.PAYMENT_PENDING,
        ],
        ConversationState.LOCATION_CAPTURE: [
            ConversationState.IDLE,
            ConversationState.PAYMENT_PENDING,
        ],
        ConversationState.PAYMENT_PENDING: [
            ConversationState.IDLE,
            ConversationState.SETTLEMENT,
        ],
        ConversationState.ACTIVE_CLAIM: [
            ConversationState.IDLE,
            ConversationState.DOCUMENT_UPLOAD,
            ConversationState.SUPPORT,
        ],
        ConversationState.DOCUMENT_UPLOAD: [
            ConversationState.IDLE,
            ConversationState.FRAUD_REVIEW,
            ConversationState.ACTIVE_CLAIM,
        ],
        ConversationState.FRAUD_REVIEW: [
            ConversationState.IDLE,
            ConversationState.ACTIVE_CLAIM,
            ConversationState.SETTLEMENT,
        ],
        ConversationState.SETTLEMENT: [
            ConversationState.IDLE,
        ],
        ConversationState.SUPPORT: [
            ConversationState.IDLE,
        ],
    }
    
    # States that require explicit user confirmation to exit
    CONFIRMATION_REQUIRED: List[ConversationState] = [
        ConversationState.PARENT_CONFIRMATION,
        ConversationState.PAYMENT_PENDING,
    ]
    
    # Timeout in hours
    TIMEOUT_HOURS = 24
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._handlers: Dict[ConversationState, List[Callable]] = {}
        self._transition_handlers: Dict[tuple, List[Callable]] = {}
    
    def can_transition(
        self, 
        from_state: ConversationState, 
        to_state: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a state transition is valid.
        
        Special rules:
        - Cannot skip PARENT_CONFIRMATION if family plan selected
        - Must have opted_in for most states
        """
        # Check basic transition validity
        valid_next_states = self.TRANSITIONS.get(from_state, [])
        if to_state not in valid_next_states:
            return False
        
        # CIMA Rule: Cannot skip PARENT_CONFIRMATION for family plans
        if context and context.get("plan_type") == "family":
            if from_state == ConversationState.PLAN_SELECTION:
                if to_state != ConversationState.PARENT_CONFIRMATION:
                    logger.warning(
                        "Blocked transition: Family plan requires PARENT_CONFIRMATION"
                    )
                    return False
        
        return True
    
    def transition(
        self,
        conversation: WhatsAppConversation,
        to_state: ConversationState,
        context_update: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
        force: bool = False
    ) -> WhatsAppConversation:
        """
        Execute a state transition.
        
        Args:
            conversation: Current conversation
            to_state: Target state
            context_update: Data to add to context
            message_id: For idempotency check
            force: Bypass validation (admin only)
        
        Returns:
            Updated conversation
        
        Raises:
            StateTransitionError: If transition is invalid
            StateTimeoutError: If conversation has timed out
        """
        # Check timeout
        if self.is_timed_out(conversation):
            # Reset to IDLE
            logger.info(f"Conversation {conversation.phone} timed out, resetting to IDLE")
            conversation.state = ConversationState.IDLE
            conversation.context["timeout_occurred"] = True
            
            # Notify handlers
            self._notify_transition_handlers(
                conversation, 
                ConversationState.IDLE,
                timeout=True
            )
        
        from_state = conversation.state
        
        # Idempotency check
        if message_id and not force:
            if self._is_duplicate_message(conversation, message_id):
                logger.debug(f"Duplicate message {message_id} ignored")
                return conversation
        
        # Validate transition
        if not force and not self.can_transition(from_state, to_state, conversation.context):
            raise StateTransitionError(
                f"Invalid transition from {from_state} to {to_state}"
            )
        
        # Check if confirmation is required for current state
        if from_state in self.CONFIRMATION_REQUIRED and not force:
            if not context_update or not context_update.get("confirmed"):
                raise StateTransitionError(
                    f"Confirmation required to exit {from_state}"
                )
        
        # Execute transition
        old_state = conversation.state
        conversation.state = to_state
        conversation.last_interaction = datetime.utcnow()
        
        # Update context
        if context_update:
            conversation.context.update(context_update)
        
        # Track message for idempotency
        if message_id:
            self._track_message(conversation, message_id)
        
        # Update Redis TTL
        self._update_redis_ttl(conversation)
        
        # Notify handlers
        self._notify_transition_handlers(conversation, old_state)
        
        logger.info(
            f"State transition: {old_state} -> {to_state} for {conversation.phone}"
        )
        
        return conversation
    
    def is_timed_out(self, conversation: WhatsAppConversation) -> bool:
        """Check if conversation has timed out (24 hours)."""
        if not conversation.last_interaction:
            return False
        
        timeout_threshold = datetime.utcnow() - timedelta(hours=self.TIMEOUT_HOURS)
        return conversation.last_interaction < timeout_threshold
    
    def get_timeout_remaining(self, conversation: WhatsAppConversation) -> Optional[int]:
        """Get remaining seconds before timeout."""
        if not conversation.last_interaction:
            return None
        
        timeout_at = conversation.last_interaction + timedelta(hours=self.TIMEOUT_HOURS)
        remaining = (timeout_at - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
    
    def _is_duplicate_message(
        self, 
        conversation: WhatsAppConversation, 
        message_id: str
    ) -> bool:
        """Check if message was already processed (idempotency)."""
        if not self.redis:
            return False  # Cannot check without Redis
        
        key = f"whatsapp:processed:{conversation.phone}:{message_id}"
        return self.redis.exists(key) > 0
    
    def _track_message(
        self, 
        conversation: WhatsAppConversation, 
        message_id: str
    ):
        """Track message for idempotency (Redis with TTL)."""
        if not self.redis:
            return
        
        key = f"whatsapp:processed:{conversation.phone}:{message_id}"
        # Store for 48 hours (2x timeout window)
        self.redis.setex(key, timedelta(hours=48), "1")
    
    def _update_redis_ttl(self, conversation: WhatsAppConversation):
        """Update conversation state TTL in Redis."""
        if not self.redis:
            return
        
        key = f"whatsapp:state:{conversation.phone}"
        state_data = {
            "state": conversation.state.value,
            "context": conversation.context,
            "last_interaction": conversation.last_interaction.isoformat(),
        }
        
        # Set TTL to 24 hours
        self.redis.setex(
            key, 
            timedelta(hours=self.TIMEOUT_HOURS),
            str(state_data)
        )
    
    def restore_from_redis(self, phone: str) -> Optional[Dict[str, Any]]:
        """Restore conversation state from Redis."""
        if not self.redis:
            return None
        
        key = f"whatsapp:state:{phone}"
        data = self.redis.get(key)
        
        if data:
            import json
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                # Handle the string representation format
                import ast
                try:
                    return ast.literal_eval(data)
                except:
                    return None
        return None
    
    # Handler registration
    def on_state(self, state: ConversationState):
        """Decorator to register a handler for a specific state."""
        def decorator(func: Callable):
            if state not in self._handlers:
                self._handlers[state] = []
            self._handlers[state].append(func)
            return func
        return decorator
    
    def on_transition(self, from_state: ConversationState, to_state: ConversationState):
        """Decorator to register a handler for a specific transition."""
        def decorator(func: Callable):
            key = (from_state, to_state)
            if key not in self._transition_handlers:
                self._transition_handlers[key] = []
            self._transition_handlers[key].append(func)
            return func
        return decorator
    
    def _notify_transition_handlers(
        self, 
        conversation: WhatsAppConversation, 
        old_state: ConversationState,
        timeout: bool = False
    ):
        """Notify registered handlers of state transition."""
        # Notify state-specific handlers
        handlers = self._handlers.get(conversation.state, [])
        for handler in handlers:
            try:
                handler(conversation, old_state, timeout=timeout)
            except Exception as e:
                logger.error(f"State handler error: {e}")
        
        # Notify transition-specific handlers
        key = (old_state, conversation.state)
        transition_handlers = self._transition_handlers.get(key, [])
        for handler in transition_handlers:
            try:
                handler(conversation, timeout=timeout)
            except Exception as e:
                logger.error(f"Transition handler error: {e}")


# State-specific context validators
class ContextValidator:
    """Validate context data for specific states."""
    
    @staticmethod
    def validate_trade_selection(context: Dict[str, Any]) -> bool:
        """Validate trade selection context."""
        valid_trades = [
            "menuisier", "mecanicien", "electricien", "plombier",
            "macon", "peintre", "soudeur", "coiffeur", "tailleur",
            "vendeur", "autre"
        ]
        trade = context.get("trade")
        return trade in valid_trades
    
    @staticmethod
    def validate_plan_selection(context: Dict[str, Any]) -> bool:
        """Validate plan selection context."""
        valid_plans = ["individual", "family", "group"]
        plan = context.get("plan_type")
        return plan in valid_plans
    
    @staticmethod
    def validate_parent_confirmation(context: Dict[str, Any]) -> bool:
        """Validate parental coverage confirmation (CIMA requirement)."""
        if context.get("plan_type") != "family":
            return True  # Not required for non-family plans
        
        # Must have explicit confirmation for both parents
        confirmed = context.get("parents_confirmed", False)
        covers_parents = context.get("covers_parents", False)
        
        return confirmed and covers_parents
    
    @staticmethod
    def validate_location(context: Dict[str, Any]) -> bool:
        """Validate location capture."""
        lat = context.get("latitude")
        lng = context.get("longitude")
        
        if lat is None or lng is None:
            return False
        
        # Validate Ivory Coast bounds (approximately)
        # Latitude: 4°N to 11°N
        # Longitude: 8°W to 3°W
        try:
            lat_f = float(lat)
            lng_f = float(lng)
            return 4.0 <= lat_f <= 11.0 and -8.0 <= lng_f <= -3.0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_payment(context: Dict[str, Any]) -> bool:
        """Validate payment context."""
        required_fields = ["amount", "currency", "payment_method"]
        return all(context.get(field) for field in required_fields)


def require_confirmation(state_machine: StateMachine):
    """Decorator to require explicit confirmation before state change."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(conversation: WhatsAppConversation, *args, **kwargs):
            if conversation.state in StateMachine.CONFIRMATION_REQUIRED:
                if not conversation.context.get("confirmed"):
                    raise StateTransitionError(
                        f"Confirmation required for {conversation.state}"
                    )
            return func(conversation, *args, **kwargs)
        return wrapper
    return decorator
