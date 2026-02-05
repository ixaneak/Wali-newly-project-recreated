"""
Security Tests for Policy Service
Verifies that protected endpoints reject unauthenticated requests.
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Health endpoint should be accessible without authentication."""
    
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestProtectedEndpoints:
    """Protected endpoints should return 401 without valid JWT token."""
    
    # Policy endpoints
    def test_create_policy_requires_auth(self):
        response = client.post("/api/v1/policies/", json={
            "user_id": "test-user",
            "coverage_type": "health",
            "coverage_details": {"max_coverage_amount": 100000},
            "payment_frequency": "daily"
        })
        assert response.status_code == 401
    
    def test_get_policy_requires_auth(self):
        response = client.get("/api/v1/policies/some-id")
        assert response.status_code == 401
    
    def test_list_policies_requires_admin(self):
        response = client.get("/api/v1/policies/")
        assert response.status_code == 401
    
    # Claims endpoints
    def test_create_claim_requires_auth(self):
        response = client.post("/api/v1/claims", json={
            "claim_type": "medical",
            "amount": 50000,
            "description": "Test claim description",
            "incident_date": "2026-01-01"
        })
        assert response.status_code == 401
    
    def test_get_claims_requires_auth(self):
        response = client.get("/api/v1/claims")
        assert response.status_code == 401
    
    def test_admin_claims_requires_auth(self):
        response = client.get("/api/v1/claims/admin/all")
        assert response.status_code == 401
    
    # Photo endpoints
    def test_upload_photo_requires_auth(self):
        response = client.post("/api/v1/photos/upload")
        assert response.status_code == 401
    
    # Admin user endpoints
    def test_admin_users_requires_auth(self):
        response = client.get("/api/v1/users/admin")
        assert response.status_code == 401
    
    # Compliance endpoints
    def test_audit_trail_requires_auth(self):
        response = client.get("/api/v1/compliance/audit-trail")
        assert response.status_code == 401
    
    def test_compliance_stats_requires_auth(self):
        response = client.get("/api/v1/compliance/stats")
        assert response.status_code == 401


class TestRootEndpoint:
    """Root endpoint should be accessible without authentication."""
    
    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Wali Policy Service" in response.json()["service"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
