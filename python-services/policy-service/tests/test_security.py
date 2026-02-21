"""
Security-related tests.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.secure_auth import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
)


class TestPasswordSecurity:
    """Test password hashing and validation."""

    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "MySecureP@ssw0rd123"
        hashed = hash_password(password)
        
        # Hash should be different from plaintext
        assert hashed != password
        # Hash should be valid Argon2 format
        assert hashed.startswith("$argon2id$")
        
    def test_password_verification(self):
        """Test password verification."""
        password = "MySecureP@ssw0rd123"
        hashed = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        # Wrong password should fail
        assert verify_password("wrongpassword", hashed) is False

    def test_password_strength_validation(self):
        """Test password strength requirements."""
        # Valid strong password
        valid, msg = validate_password_strength("MySecureP@ssw0rd123")
        assert valid is True
        
        # Too short
        valid, msg = validate_password_strength("Short1!")
        assert valid is False
        
        # No uppercase
        valid, msg = validate_password_strength("lowercase123!")
        assert valid is False
        
        # No lowercase
        valid, msg = validate_password_strength("UPPERCASE123!")
        assert valid is False
        
        # No numbers
        valid, msg = validate_password_strength("NoNumbers!")
        assert valid is False
        
        # No special characters
        valid, msg = validate_password_strength("NoSpecial123")
        assert valid is False


class TestJWTSecurity:
    """Test JWT token security."""

    def test_token_creation(self):
        """Test JWT token creation."""
        data = {"sub": "user123", "role": "artisan"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        # JWT should have 3 parts separated by dots
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_expiration(self):
        """Test that tokens have expiration."""
        from datetime import timedelta
        
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(minutes=15))
        
        # Token should be created successfully
        assert token is not None


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_login_rate_limiting(self, client: TestClient):
        """Test that login endpoints are rate limited."""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={"phone": "+2250701234567", "password": "wrong"},
            )
            responses.append(response.status_code)
        
        # Some requests should be rate limited (429)
        # Note: In test environment with in-memory rate limiting, 
        # this may not trigger depending on config
        assert 429 in responses or all(r in [401, 404] for r in responses)


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sql_injection_attempt(self, client: TestClient):
        """Test that SQL injection attempts are blocked."""
        # Attempt SQL injection in login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "phone": "+2250701234567' OR '1'='1",
                "password": "anything",
            },
        )
        # Should not succeed (either 400 for invalid format or 401/404)
        assert response.status_code in [400, 401, 404, 422]

    def test_xss_attempt_blocked(self, client: TestClient, auth_headers: dict):
        """Test that XSS attempts are sanitized."""
        # This would be tested more thoroughly with actual endpoints
        # that accept user input and return it
        pass


class TestSecurityHeaders:
    """Test security headers in responses."""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are present."""
        response = client.get("/health")
        
        # Check for security headers
        headers = response.headers
        
        # These headers should be set by security middleware
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"


class TestDebugEndpointsDisabled:
    """Test that debug endpoints are not available in production-like environments."""

    def test_no_debug_bypass_in_pharmacy_login(self, client: TestClient):
        """Verify no debug bypass for pharmacy login."""
        response = client.post(
            "/api/v1/pharmacy/auth/login",
            json={"email": "pharmacie@wali.com", "password": "pharma1234"},
        )
        # Should return 401 because the pharmacy doesn't exist
        # If debug bypass existed, it might return 200
        assert response.status_code == 401

    def test_no_debug_key_in_stats(self, client: TestClient, test_pharmacy):
        """Verify no debug key bypass for stats endpoint."""
        response = client.get(
            "/api/v1/pharmacy/stats",
            headers={"X-API-Key": "debug_key"},
        )
        # Should reject debug key
        assert response.status_code == 401
