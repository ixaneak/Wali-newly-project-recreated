"""
Pytest configuration and fixtures for Wali Policy Service tests.
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, get_db
from app.main import app
from app.models.policy import User, UserRole, KYCStatus
from app.models.pharmacy import PharmacyPartner, SubscriptionStatus
from app.core.secure_auth import hash_password

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    yield TestClient(app)


@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        id="test-user-id-123",
        phone="+2250701234567",
        email="test@example.com",
        name="Test User",
        role=UserRole.ARTISAN,
        kyc_status=KYCStatus.VERIFIED,
        region="Abidjan",
        password_hash=hash_password("testpassword123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin(db: Session) -> User:
    """Create a test admin user."""
    admin = User(
        id="test-admin-id-456",
        phone="+2250709876543",
        email="admin@wali.ci",
        name="Test Admin",
        role=UserRole.ADMIN,
        kyc_status=KYCStatus.VERIFIED,
        region="Abidjan",
        password_hash=hash_password("adminpassword123"),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def test_pharmacy(db: Session) -> PharmacyPartner:
    """Create a test pharmacy partner."""
    pharmacy = PharmacyPartner(
        id="test-pharmacy-id-789",
        email="pharmacy@example.com",
        password_hash=hash_password("pharmacypassword123"),
        business_name="Test Pharmacy",
        subscription_status=SubscriptionStatus.ACTIVE,
        api_key="test-api-key-12345",
        trial_ends_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(pharmacy)
    db.commit()
    db.refresh(pharmacy)
    return pharmacy


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": test_user.phone, "password": "testpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client: TestClient, test_admin: User) -> dict:
    """Get authentication headers for admin user."""
    response = client.post(
        "/auth/admin/login",
        json={"email": test_admin.email, "password": "adminpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
