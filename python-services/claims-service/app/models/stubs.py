"""
Stub models for ForeignKey references from other services.
Updated for SaaS model: policies→coverage_subscriptions.
"""
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid


class User(Base):
    __tablename__ = "users"
    id = Column(String(128), primary_key=True)


class CoverageSubscription(Base):
    """Stub for policy-service's coverage_subscriptions table."""
    __tablename__ = "coverage_subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# Backward compatibility
Policy = CoverageSubscription
