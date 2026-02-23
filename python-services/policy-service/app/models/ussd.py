from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from app.core.database import Base

class USSDSessionLog(Base):
    """
    Audit log for USSD sessions tracking user journeys.
    """
    __tablename__ = "ussd_sessions_log"

    session_id = Column(String, primary_key=True, index=True)
    phone_number = Column(String, index=True, nullable=False)
    network_code = Column(String, nullable=True)
    duration = Column(Integer, default=0, doc="Duration in seconds")
    screens_visited = Column(Integer, default=1)
    final_state = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
