"""Test that unauthenticated requests return 401."""
import requests

BASE_URL = "http://127.0.0.1:8001"

print("=" * 50)
print("SECURITY VERIFICATION TEST")
print("=" * 50)

# Test 1: POST /api/v1/claims/submit-json without token
print("\nTest 1: POST /submit-json without token")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/claims/submit-json",
        json={
            "user_id": "test-user-id",
            "policy_id": "test-policy-id",
            "claim_type": "HEALTH",
            "description": "Test claim",
            "claimed_amount": 1000
        },
        timeout=5
    )
    status1 = response.status_code
    print(f"  Status: {status1}")
    print(f"  Response: {response.text[:100]}")
    pass1 = status1 == 401
    print(f"  PASS: {'YES' if pass1 else 'NO (expected 401)'}")
except Exception as e:
    print(f"  ERROR: {e}")
    pass1 = False

# Test 2: GET /api/v1/claims/admin/all without token (admin endpoint)
print("\nTest 2: GET /admin/all without token")
try:
    response = requests.get(f"{BASE_URL}/api/v1/claims/admin/all", timeout=5)
    status2 = response.status_code
    print(f"  Status: {status2}")
    print(f"  Response: {response.text[:100]}")
    pass2 = status2 == 401
    print(f"  PASS: {'YES' if pass2 else 'NO (expected 401)'}")
except Exception as e:
    print(f"  ERROR: {e}")
    pass2 = False

# Test 3: Health check (should NOT require auth)
print("\nTest 3: GET /health without token (should pass)")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    status3 = response.status_code
    print(f"  Status: {status3}")
    pass3 = status3 == 200
    print(f"  PASS: {'YES' if pass3 else 'NO (expected 200)'}")
except Exception as e:
    print(f"  ERROR: {e}")
    pass3 = False

print("\n" + "=" * 50)
all_pass = pass1 and pass2 and pass3
print(f"OVERALL: {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
print("=" * 50)
