"""
PayDunya Integration Tests

Tests hash verification, configuration, provider detection,
and internal reference generation WITHOUT requiring a database
or PayDunya API access.
"""
import hashlib
import sys
import os

# Ensure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_hash_verification_valid():
    """Valid hash should pass verification."""
    from app.config.paydunya import verify_paydunya_hash

    private_key = "test_private_key_123"
    token = "inv_abc123"
    status = "completed"

    # Compute expected hash the same way PayDunya does
    raw = f"{token}{status}{private_key}"
    expected_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    payload = {
        "data": {
            "hash": expected_hash,
            "invoice": {
                "token": token,
                "status": status,
            },
        }
    }

    assert verify_paydunya_hash(payload, private_key) is True
    print("[PASS] test_hash_verification_valid")


def test_hash_verification_invalid():
    """Tampered hash should fail verification."""
    from app.config.paydunya import verify_paydunya_hash

    payload = {
        "data": {
            "hash": "tampered_hash_value_000000",
            "invoice": {
                "token": "inv_abc123",
                "status": "completed",
            },
        }
    }

    assert verify_paydunya_hash(payload, "test_private_key_123") is False
    print("[PASS] test_hash_verification_invalid")


def test_hash_verification_empty_payload():
    """Empty / malformed payload should return False, not crash."""
    from app.config.paydunya import verify_paydunya_hash

    assert verify_paydunya_hash({}, "key") is False
    assert verify_paydunya_hash({"data": {}}, "key") is False
    assert verify_paydunya_hash({"data": {"hash": ""}}, "key") is False
    assert verify_paydunya_hash(None, "key") is False  # type: ignore
    print("[PASS] test_hash_verification_empty_payload")


def test_hash_verification_missing_fields():
    """Payload with hash but missing invoice fields should fail gracefully."""
    from app.config.paydunya import verify_paydunya_hash

    payload = {
        "data": {
            "hash": "somehash",
            # no "invoice" key
        }
    }
    assert verify_paydunya_hash(payload, "key") is False
    print("[PASS] test_hash_verification_missing_fields")


def test_config_loads():
    """PayDunya config should load with defaults in test mode."""
    from app.config.paydunya import paydunya_config

    assert paydunya_config.MODE == "test"
    assert "sandbox" in paydunya_config.BASE_URL
    assert paydunya_config.api_url == paydunya_config.BASE_URL
    assert "PAYDUNYA-MASTER-KEY" in paydunya_config.headers
    assert "PAYDUNYA-PRIVATE-KEY" in paydunya_config.headers
    assert "PAYDUNYA-PUBLIC-KEY" in paydunya_config.headers
    print("[PASS] test_config_loads")


def test_provider_detection():
    """Phone number prefix should map to correct mobile money provider."""
    from app.services.paydunya_service import detect_provider_from_phone

    assert detect_provider_from_phone("+225 07 12 34 56 78") == "orange_money"
    assert detect_provider_from_phone("+225 08 12 34 56 78") == "orange_money"
    assert detect_provider_from_phone("+225 05 12 34 56 78") == "mtn_momo"
    assert detect_provider_from_phone("+225 06 12 34 56 78") == "mtn_momo"
    assert detect_provider_from_phone("+225 01 12 34 56 78") == "moov"
    assert detect_provider_from_phone("+225 09 12 34 56 78") == "wave"
    assert detect_provider_from_phone("+225 02 12 34 56 78") == "unknown"
    # Without country code
    assert detect_provider_from_phone("07 12 34 56 78") == "orange_money"
    print("[PASS] test_provider_detection")


def test_internal_ref_format():
    """Internal reference should follow WALI-YYYYMMDD-XXXXXX format."""
    from app.services.paydunya_service import generate_internal_ref
    import re

    ref = generate_internal_ref()
    pattern = r"^WALI-\d{8}-[A-F0-9]{6}$"
    assert re.match(pattern, ref), f"Ref '{ref}' doesn't match pattern {pattern}"
    print("[PASS] test_internal_ref_format")



    print("[PASS] test_premium_calculation")


def test_provider_detection_from_payload():
    """Detect provider from a PayDunya webhook payload."""
    from app.services.paydunya_service import detect_provider_from_payload

    payload = {
        "data": {
            "customer": {
                "phone": "+225 07 12 34 56"
            }
        }
    }
    assert detect_provider_from_payload(payload) == "orange_money"

    empty_payload = {"data": {"customer": {}}}
    assert detect_provider_from_payload(empty_payload) == "unknown"
    print("[PASS] test_provider_detection_from_payload")


def test_transaction_model_to_dict():
    """PaydunyaTransaction.to_dict() should return a clean dictionary."""
    from app.models.paydunya_transaction import PaydunyaTransaction
    import uuid

    txn = PaydunyaTransaction(
        id=uuid.uuid4(),
        internal_ref="WALI-20260210-ABC123",
        amount=4500,
        status="pending",
    )
    d = txn.to_dict()
    assert d["internal_ref"] == "WALI-20260210-ABC123"
    assert d["amount"] == 4500
    assert d["status"] == "pending"
    assert d["paydunya_token"] is None
    print("[PASS] test_transaction_model_to_dict")


# ==================== Runner ====================

if __name__ == "__main__":
    tests = [
        test_hash_verification_valid,
        test_hash_verification_invalid,
        test_hash_verification_empty_payload,
        test_hash_verification_missing_fields,
        test_config_loads,
        test_provider_detection,
        test_internal_ref_format,
        test_premium_calculation,
        test_provider_detection_from_payload,
        test_transaction_model_to_dict,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_fn.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed > 0:
        sys.exit(1)
    else:
        print("All PayDunya tests passed! ✓")
