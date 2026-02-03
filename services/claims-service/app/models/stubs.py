from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(String(128), primary_key=True)

class Policy(Base):
    __tablename__ = "policies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
