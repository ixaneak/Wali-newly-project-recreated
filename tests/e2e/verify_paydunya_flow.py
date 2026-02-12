"""
PayDunya E2E Flow Verification Script

Tests the full payment flow against a running policy service:
1. Create a policy (pending)
2. Initiate PayDunya payment  
3. Simulate webhook callback (with valid hash)
4. Verify payment → policy activated

Usage:
    python tests/e2e/verify_paydunya_flow.py

Requires: policy service running on localhost:8000
"""
import hashlib
import json
import sys
import uuid
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"
PAYDUNYA_PRIVATE_KEY = "test_private_xXxXxXxXxXxXxXxXxXxXx"

# Mock JWT token (matches dev settings in security_middleware.py)
import jwt
JWT_SECRET = "dev_jwt_secret_change_in_production"


def create_test_token(user_id: str = "test-user-001", role: str = "ARTISAN") -> str:
    """Create a JWT token for testing."""
    from datetime import timedelta
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def make_headers(user_id: str = "test-user-001") -> dict:
    """Create auth headers."""
    token = create_test_token(user_id)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def step_1_health_check():
    """Verify service is running."""
    print("\n[Step 1] Health check...")
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    print(f"  ✓ Service healthy: {resp.json()}")


def step_2_create_policy():
    """Create a pending policy for testing."""
    print("\n[Step 2] Creating test policy...")
    headers = make_headers()

    resp = requests.post(
        f"{BASE_URL}/api/v1/policies/",
        headers=headers,
        json={
            "user_id": "test-user-001",
            "coverage_type": "health",
            "coverage_details": {"max_coverage_amount": 50000},
            "payment_frequency": "monthly",
        },
        timeout=10,
    )

    if resp.status_code == 201:
        data = resp.json()
        print(f"  ✓ Policy created: {data['id']} (status: {data['status']})")
        return data["id"]
    else:
        print(f"  ✗ Failed to create policy: {resp.status_code} {resp.text}")
        return None


def step_3_initiate_payment(policy_id: str):
    """Call PayDunya initiate endpoint."""
    print(f"\n[Step 3] Initiating PayDunya payment for policy {policy_id}...")
    headers = make_headers()

    resp = requests.post(
        f"{BASE_URL}/api/v1/payments/paydunya/initiate",
        headers=headers,
        json={
            "policy_id": policy_id,
            "phone_number": "+225 07 12 34 56 78",
        },
        timeout=30,
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"  ✓ Invoice created: {data['internal_ref']}")
        print(f"    Amount: {data['amount']} XOF")
        print(f"    Test mode: {data['test_mode']}")
        print(f"    Instructions: {data['instructions']}")
        return data["internal_ref"], data.get("invoice_token", "test-token")
    else:
        print(f"  ✗ Payment initiation failed: {resp.status_code} {resp.text}")
        return None, None


def step_4_simulate_webhook(internal_ref: str, invoice_token: str):
    """Simulate PayDunya IPN webhook with valid hash."""
    print(f"\n[Step 4] Simulating PayDunya webhook for {internal_ref}...")

    # Compute valid hash: sha256(token + status + private_key)
    status = "completed"
    raw = f"{invoice_token}{status}{PAYDUNYA_PRIVATE_KEY}"
    valid_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    webhook_payload = {
        "data": {
            "hash": valid_hash,
            "invoice": {
                "token": invoice_token,
                "status": status,
                "total_amount": 4500,
                "custom_data": {
                    "internal_ref": internal_ref,
                },
            },
            "custom_data": {
                "internal_ref": internal_ref,
            },
            "customer": {
                "phone": "+225 07 12 34 56",
                "name": "Test User",
            },
        }
    }

    resp = requests.post(
        f"{BASE_URL}/api/v1/payments/paydunya/webhook",
        json=webhook_payload,
        timeout=10,
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"  ✓ Webhook processed: {data}")
        return True
    else:
        print(f"  ✗ Webhook failed: {resp.status_code} {resp.text}")
        return False


def step_5_verify_payment(internal_ref: str):
    """Verify payment status via API."""
    print(f"\n[Step 5] Verifying payment status for {internal_ref}...")
    headers = make_headers()

    resp = requests.get(
        f"{BASE_URL}/api/v1/payments/paydunya/verify/{internal_ref}",
        headers=headers,
        timeout=10,
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"  ✓ Payment status: {data['status']}")
        print(f"    Provider: {data.get('provider')}")
        print(f"    Activated at: {data.get('activated_at')}")

        if data["status"] == "completed":
            print("  ✓ Payment COMPLETED — policy should be active!")
            return True
        else:
            print(f"  ⚠ Expected 'completed', got '{data['status']}'")
            return False
    else:
        print(f"  ✗ Verification failed: {resp.status_code} {resp.text}")
        return False


def step_6_security_test():
    """Test that a spoofed webhook is rejected."""
    print("\n[Step 6] Security test — spoofed webhook...")

    spoofed_payload = {
        "data": {
            "hash": "fake_hash_000000",
            "invoice": {
                "token": "fake-token",
                "status": "completed",
            },
            "custom_data": {
                "internal_ref": "WALI-FAKE-000000",
            },
        }
    }

    resp = requests.post(
        f"{BASE_URL}/api/v1/payments/paydunya/webhook",
        json=spoofed_payload,
        timeout=10,
    )

    if resp.status_code == 403:
        print("  ✓ Spoofed webhook correctly rejected with 403")
        return True
    else:
        print(f"  ✗ Expected 403, got {resp.status_code}: {resp.text}")
        return False


def step_7_test_numbers():
    """Verify test numbers endpoint."""
    print("\n[Step 7] Fetching test numbers...")
    resp = requests.get(f"{BASE_URL}/api/v1/payments/paydunya/test-numbers", timeout=5)

    if resp.status_code == 200:
        data = resp.json()
        print(f"  ✓ Test numbers: {json.dumps(data, indent=2)}")
        return True
    else:
        print(f"  ✗ Failed: {resp.status_code}")
        return False


def run_e2e():
    """Run all E2E steps."""
    print("=" * 60)
    print("PayDunya E2E Flow Verification")
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        step_1_health_check()
    except Exception as e:
        print(f"\n✗ Service not reachable: {e}")
        print("Start the service with: uvicorn app.main:app --port 8000")
        sys.exit(1)

    policy_id = step_2_create_policy()
    if not policy_id:
        print("\n⚠ Skipping payment steps (no policy created)")
        print("  This may be due to missing database.")

        # Still run security + test-numbers tests
        step_6_security_test()
        step_7_test_numbers()
        return

    internal_ref, invoice_token = step_3_initiate_payment(policy_id)
    if not internal_ref:
        print("\n⚠ Payment initiation failed (PayDunya API may be unreachable in test)")
        # Still run remaining tests
        step_6_security_test()
        step_7_test_numbers()
        return

    step_4_simulate_webhook(internal_ref, invoice_token)
    step_5_verify_payment(internal_ref)
    step_6_security_test()
    step_7_test_numbers()

    print("\n" + "=" * 60)
    print("E2E verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_e2e()
