import json
import redis
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import get_settings

settings = get_settings()

class USSDSessionManager:
    def __init__(self, redis_url: str = None):
        url = redis_url if redis_url else settings.redis_url
        self.redis = redis.from_url(url, decode_responses=True)
        self.ttl = 300  # 300 seconds = 5 minutes timeout

    def normalize_phone(self, phone: str) -> str:
        """Normalize phone to E.164 format (+225XXXXXXXXX)."""
        phone = phone.strip()
        if phone.startswith('0') and len(phone) == 10:
            return f"+225{phone}"
        if not phone.startswith('+'):
            return f"+{phone}"
        return phone

    def _get_key(self, session_id: str) -> str:
        return f"ussd:session:{session_id}"

    def get_or_create_session(self, session_id: str, phone: str) -> Dict[str, Any]:
        """Check Redis, if exists return, else create new with state='welcome'."""
        key = self._get_key(session_id)
        
        existing_data = self.redis.get(key)
        if existing_data:
            # Refresh TTL on access
            self.redis.expire(key, self.ttl)
            return json.loads(existing_data)
        
        # Create new session
        new_session = {
            "phone": self.normalize_phone(phone),
            "state": "welcome",
            "context": {
                "selected_plan": None,
                "trade_category": None,
                "claim_reference": None,
                "awaiting_payment": False
            },
            "history": ["welcome"],  # For "Retour" navigation
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.redis.setex(key, self.ttl, json.dumps(new_session))
        return new_session

    def update_state(self, session_id: str, new_state: str, context_updates: Dict[str, Any] = None) -> Dict[str, Any]:
        """Atomic update via Redis pipeline. Append old state to history."""
        key = self._get_key(session_id)
        
        # We need to read, modify, and write.
        # While watch/pipeline could be used, USSD sessions are per-user synchronous.
        existing_data = self.redis.get(key)
        if not existing_data:
            return None
            
        session = json.loads(existing_data)
        
        current_state = session.get("state")
        if current_state != new_state:
            # Append old state to history (Max 5 levels)
            history = session.get("history", [])
            if not history or history[-1] != current_state:
                history.append(current_state)
            
            # Keep max 5 levels
            session["history"] = history[-5:]
            
            session["state"] = new_state
            
        if context_updates:
            session["context"].update(context_updates)
            
        # Update redis atomically where possible, but here we just set it back
        self.redis.setex(key, self.ttl, json.dumps(session))
        
        return session

    def get_previous_state(self, session_id: str) -> str:
        """Pop from history for '0. Retour' functionality."""
        key = self._get_key(session_id)
        existing_data = self.redis.get(key)
        if not existing_data:
            return "welcome"
            
        session = json.loads(existing_data)
        history = session.get("history", [])
        
        if len(history) > 1:
            # Remove current state if it's there, pop the previous
            history.pop()  # Pop current state (or last known)
            previous_state = history[-1] if history else "welcome"
        else:
            previous_state = "welcome"
            
        session["history"] = history
        session["state"] = previous_state
        self.redis.setex(key, self.ttl, json.dumps(session))
        
        return previous_state

    def clear_session(self, session_id: str):
        """Delete key (user dials exit or timeout)."""
        key = self._get_key(session_id)
        self.redis.delete(key)
