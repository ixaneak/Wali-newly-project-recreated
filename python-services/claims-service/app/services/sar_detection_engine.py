from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class RiskEvent:
    risk_score: float = 0.0
    tags: list = None
    
    def to_dict(self):
        return asdict(self)

class SARDetectionEngine:
    def __init__(self, db_session=None):
        self.db = db_session

    async def analyze_claim(self, claim_data: Dict[str, Any]) -> RiskEvent:
        # Mock implementation always returns low risk
        return RiskEvent(risk_score=0.0, tags=[])

class DetectionRuleType:
    VELOCITY = "velocity"
    AMOUNT = "amount"
