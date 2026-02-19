"""
SAR End-to-End Integration Tests
Run: python tests/test_sar_e2e.py
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from app.core.security_middleware_v2 import create_test_token

BASE = "http://localhost:8000/api/v1/compliance/sar"
TOKEN = create_test_token("admin-e2e-001", role="ADMIN", expires_minutes=60)
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  PASS: {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {name}: {e}")
        failed += 1

# TEST 1: Rapid Claim Detection
print("\n--- TEST 1: Rapid Claim Detection ---")

def test_rapid_claim():
    r = requests.post(f"{BASE}/scan-transaction", headers=HEADERS, json={
        "user_id": "user-rapid-001",
        "amount": 490000,
        "phone": "+22501010101",
        "claim_created_at": "2026-02-18T12:00:00Z"
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    result = data["scoring_result"]
    rules = [r["rule"] for r in result["triggered_rules"]]
    print(f"    Score: {result['risk_score']}, Severity: {result['severity']}")
    print(f"    Rules fired: {rules}")
    assert result["rules_fired"] > 0, "No rules fired"

test("Scan detects rapid claim", test_rapid_claim)

# TEST 2: Threshold Breach Detection
print("\n--- TEST 2: Threshold Breach Detection ---")

def test_threshold():
    r = requests.post(f"{BASE}/scan-transaction", headers=HEADERS, json={
        "user_id": "user-threshold-001",
        "amount": 600000,
        "phone": "+22502020202"
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    result = data["scoring_result"]
    rules = [r["rule"] for r in result["triggered_rules"]]
    print(f"    Score: {result['risk_score']}, Severity: {result['severity']}")
    print(f"    Rules fired: {rules}")
    assert "threshold_breach" in rules, f"threshold_breach not in {rules}"

test("600K XOF triggers threshold breach", test_threshold)

# TEST 3: Round Number + Identity Mismatch combo
print("\n--- TEST 3: Round Number Detection ---")

def test_combo():
    r = requests.post(f"{BASE}/scan-transaction", headers=HEADERS, json={
        "user_id": "user-combo-001",
        "amount": 100000,
        "phone": "+22503030303"
    })
    assert r.status_code == 200
    data = r.json()
    result = data["scoring_result"]
    rules = [r["rule"] for r in result["triggered_rules"]]
    print(f"    Score: {result['risk_score']}, Severity: {result['severity']}")
    print(f"    Rules fired: {rules}")
    assert "round_number" in rules, f"round_number not in {rules}"

test("100K round number detected", test_combo)

# TEST 4: Third-Party Payment
print("\n--- TEST 4: Third-Party Payment Detection ---")

def test_third_party():
    r = requests.post(f"{BASE}/scan-transaction", headers=HEADERS, json={
        "user_id": "user-3p-001",
        "amount": 200000,
        "payer_phone": "+22504040404",
        "policyholder_phone": "+22505050505"
    })
    assert r.status_code == 200
    data = r.json()
    result = data["scoring_result"]
    rules = [r["rule"] for r in result["triggered_rules"]]
    print(f"    Score: {result['risk_score']}, Severity: {result['severity']}")
    print(f"    Rules fired: {rules}")
    assert "third_party_payment" in rules, f"third_party_payment not in {rules}"

test("Different payer vs policyholder phones", test_third_party)

# TEST 5: Risk Events listing
print("\n--- TEST 5: Risk Events Listing ---")

def test_list_events():
    r = requests.get(f"{BASE}/risk-events", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    print(f"    Total events: {data['total']}")
    assert data["total"] >= 3, f"Expected at least 3 events, got {data['total']}"

test("List risk events from previous scans", test_list_events)

# TEST 6: Escalate to SAR Report
print("\n--- TEST 6: Escalate Risk Event to SAR ---")

sar_id = None

def test_escalate():
    global sar_id
    r = requests.get(f"{BASE}/risk-events?limit=1", headers=HEADERS)
    events = r.json()["risk_events"]
    assert len(events) > 0, "No events to escalate"
    event_id = events[0]["id"]

    r2 = requests.post(f"{BASE}/risk-events/{event_id}/escalate", headers=HEADERS, json={
        "analyst_notes": "E2E test escalation",
        "assigned_analyst": "compliance@wali.ci"
    })
    assert r2.status_code == 201, f"Expected 201, got {r2.status_code}: {r2.text}"
    sar = r2.json()["sar"]
    print(f"    SAR Reference: {sar['report_reference']}")
    print(f"    Status: {sar['status']}")
    assert sar["report_reference"].startswith("SAR-"), "Bad reference format"
    assert sar["status"] == "draft"
    sar_id = sar["id"]

test("Escalate event to formal SAR report", test_escalate)

# TEST 7: Submit to TRACFIN
print("\n--- TEST 7: Submit SAR to TRACFIN ---")

def test_tracfin():
    assert sar_id, "Need SAR ID from test 6"
    r = requests.post(f"{BASE}/reports/{sar_id}/submit-tracfin", headers=HEADERS)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    print(f"    Message: {data['message']}")
    print(f"    SAR Status: {data['sar']['status']}")
    assert data["sar"]["status"] == "submitted"
    assert "xml" in data, "No XML in response"
    assert "DeclarationSoupcon" in data["xml"], "Invalid TRACFIN XML"
    print(f"    XML length: {len(data['xml'])} chars")

test("Submit to TRACFIN and verify XML", test_tracfin)

# TEST 8: Dashboard stats
print("\n--- TEST 8: Dashboard Stats ---")

def test_dashboard():
    r = requests.get(f"{BASE}/dashboard", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    print(f"    Dashboard keys: {list(data.keys())}")

test("Dashboard endpoint returns stats", test_dashboard)

# RESULTS
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
if failed > 0:
    print("WARNING: Some tests failed!")
else:
    print("ALL TESTS PASSED!")
