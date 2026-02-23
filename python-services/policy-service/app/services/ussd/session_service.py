import json
import redis
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from app.core.config import get_settings

settings = get_settings()

try:
    # Use separate DB index for USSD to prevent collisions with rate limits/queues
    redis_client = redis.Redis.from_url(settings.redis_url, db=2, decode_responses=True)
except Exception:
    redis_client = None

@dataclass
class USSDSession:
    session_id: str
    phone_number: str
    state: str = "main_menu"
    language: str = "fr"
    context: Dict[str, Any] = field(default_factory=dict)
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class USSDSessionService:
    """
    Session Service for USSD flows with Redis TTL integration.
    """
    TTL_SECONDS = 180

    def __init__(self, r: redis.Redis = None):
        self.redis = r or redis_client
        
    def _key(self, session_id: str) -> str:
        return f"ussd:session:{session_id}"

    def get_session(self, session_id: str) -> Optional[USSDSession]:
        if not self.redis:
            return None
            
        data = self.redis.get(self._key(session_id))
        if data:
            try:
                raw_dict = json.loads(data)
                return USSDSession(**raw_dict)
            except Exception:
                pass
        return None

    def get_or_create_session(self, session_id: str, phone: str) -> USSDSession:
        if not session_id or not phone:
            return USSDSession(session_id="", phone_number="")
            
        session = self.get_session(session_id)
        if session:
            # Refresh TTL implicitly when retrieving and phone matches
            if session.phone_number == phone:
                return session

        # Create new
        new_session = USSDSession(
            session_id=session_id,
            phone_number=phone,
            state="main_menu",
            language="fr",
            context={}
        )
        self.save_session(new_session)
        return new_session

    def save_session(self, session: USSDSession) -> None:
        if not self.redis or not session.session_id:
            return
            
        session.last_activity = datetime.utcnow().isoformat()
        
        self.redis.setex(
            self._key(session.session_id),
            self.TTL_SECONDS,
            json.dumps(asdict(session))
        )
