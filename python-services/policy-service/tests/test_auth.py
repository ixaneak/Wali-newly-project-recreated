"""
Authentication and authorization tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.policy import User


class TestUserAuthentication:
    """Test user authentication flows."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful user login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": test_user.phone, "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "artisan"

    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with invalid password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": test_user.phone, "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login for non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "+2250000000000", "password": "somepassword"},
        )
        assert response.status_code == 404

    def test_login_invalid_phone_format(self, client: TestClient):
        """Test login with invalid phone format."""
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "invalid-phone", "password": "password123"},
        )
        assert response.status_code in [400, 422]


class TestAdminAuthentication:
    """Test admin authentication flows."""

    def test_admin_login_success(self, client: TestClient, test_admin: User):
        """Test successful admin login."""
        response = client.post(
            "/auth/admin/login",
            json={"email": test_admin.email, "password": "adminpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["role"] == "admin"

    def test_admin_login_invalid_password(self, client: TestClient, test_admin: User):
        """Test admin login with wrong password."""
        response = client.post(
            "/auth/admin/login",
            json={"email": test_admin.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_admin_login_non_admin_user(self, client: TestClient, test_user: User):
        """Test that non-admin users cannot use admin login."""
        response = client.post(
            "/auth/admin/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        # Should fail because test_user doesn't have admin role
        assert response.status_code in [401, 403]


class TestPharmacyAuthentication:
    """Test pharmacy authentication flows."""

    def test_pharmacy_login_success(self, client: TestClient, test_pharmacy):
        """Test successful pharmacy login."""
        response = client.post(
            "/api/v1/pharmacy/auth/login",
            json={"email": test_pharmacy.email, "password": "pharmacypassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "api_key" in data
        assert data["role"] == "pharmacy"

    def test_pharmacy_login_invalid_password(self, client: TestClient, test_pharmacy):
        """Test pharmacy login with wrong password."""
        response = client.post(
            "/api/v1/pharmacy/auth/login",
            json={"email": test_pharmacy.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_pharmacy_login_nonexistent(self, client: TestClient):
        """Test pharmacy login for non-existent email."""
        response = client.post(
            "/api/v1/pharmacy/auth/login",
            json={"email": "nonexistent@pharmacy.com", "password": "password123"},
        )
        assert response.status_code == 401

    def test_pharmacy_no_debug_bypass(self, client: TestClient):
        """Ensure debug bypass is not available."""
        # Even with development credentials, should not bypass in test environment
        response = client.post(
            "api/v1/pharmacy/auth/login",
            json={"email": "pharmacie@wali.com", "password": "pharma1234"},
        )
        # Should fail because pharmacy doesn't exist in test DB
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test access control on protected endpoints."""

    def test_access_without_token(self, client: TestClient):
        """Test that protected endpoints reject requests without token."""
        response = client.get("/api/v1/partners/test-partner/enrollments")
        assert response.status_code == 401

    def test_access_with_invalid_token(self, client: TestClient):
        """Test that invalid tokens are rejected."""
        response = client.get(
            "/api/v1/partners/test-partner/enrollments",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code in [401, 403]

    def test_admin_endpoint_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that admin endpoints require admin role."""
        # Regular user token should not work on admin endpoints
        response = client.get(
            "/api/v1/admin/users",
            headers=auth_headers,
        )
        assert response.status_code == 403
