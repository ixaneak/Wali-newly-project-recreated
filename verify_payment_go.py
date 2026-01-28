
import requests
import time
import subprocess
import os
import signal
import sys
import json

# Configuration
SERVICE_PORT = "8081" # Use different port to avoid conflict
SERVICE_DIR = "services/payment-service"
Config = {
    "PORT": SERVICE_PORT,
    "MOCK_PAYMENT_PROVIDERS": "true",
    "REDIS_URL": "redis://localhost:6379", # Ideally mock this too or ensure redis is running.
    # Go service soft fails on Redis, acceptable for this test if redis absent
}

def verify_payment_service():
    print("Starting Payment Service Verification (Mock Mode)...")
    
    # 1. Start the Go Service
    print(f"Building and starting Go service on port {SERVICE_PORT}...")
    
    # Check if go is installed
    go_path = r"C:\Program Files\Go\bin\go.exe"
    try:
        subprocess.run([go_path, "version"], check=True, capture_output=True)
    except:
        print(f"FAIL: Go executable not found at {go_path}")
        return

    # Start process
    env = os.environ.copy()
    env.update(Config)
    
    # Ensure dependencies are tidy
    print("Running go mod tidy...")
    try:
        subprocess.run([go_path, "mod", "tidy"], cwd=SERVICE_DIR, env=env, check=True)
    except:
        print("WARN: go mod tidy failed, attempting to run anyway...")

    # We use 'go run .' inside the directory
    process = subprocess.Popen(
        [go_path, "run", "."],
        cwd=SERVICE_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for service to start
        print("Waiting for service to start...")
        time.sleep(5) 
        
        # Check if process died
        if process.poll() is not None:
            print("FAIL: Service process failed to start.")
            stdout, stderr = process.communicate()
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return

        # 2. Test Health
        base_url = f"http://localhost:{SERVICE_PORT}"
        try:
            resp = requests.get(f"{base_url}/health")
            if resp.status_code == 200:
                print("PASS: Health check passed")
            else:
                print(f"FAIL: Health check failed {resp.status_code}")
        except Exception as e:
             print(f"FAIL: Health check connection error: {e}")
             return

        # 3. Test Initiate Payment (Mock)
        print("\nTest: Initiate Payment (Mock)...")
        payload = {
            "user_id": "user-123",
            "policy_id": "policy-456",
            "amount": 5000,
            "currency": "XOF",
            "phone": "+2250707070707",
            "provider": "orange"
        }
        
        resp = requests.post(f"{base_url}/api/v1/payments/initiate", json=payload)
        if resp.status_code == 201:
            data = resp.json()
            if data['status'] == 'completed' or data['status'] == 'success': # Check model constant
                 print(f"PASS: Payment initiated and completed immediately (Mock Mode). Ref: {data['transaction_ref']}")
            else:
                 print(f"WARN: Mock payment status is {data.get('status')} (Expected completed/success)")
                 # Orchestrator sets StatusSuccess which is "success"
        else:
            print(f"FAIL: Payment initiation failed {resp.status_code} - {resp.text}")

        # 4. Test Verify Payment (Mock)
        print("\nTest: Verify Payment (Mock)...")
        # In mock mode, any ref should be success
        resp = requests.get(f"{base_url}/api/v1/payments/verify/any-ref-123?provider=orange")
        if resp.status_code == 200:
            data = resp.json()
            if data['status'] == 'success':
                print("PASS: Payment verification passed")
            else:
                print(f"FAIL: Payment verification status {data.get('status')}")
        else:
            print(f"FAIL: Payment verification failed {resp.status_code}")

    finally:
        print("\nStopping service...")
        process.terminate()
        # Ensure it's dead
        try:
            process.wait(timeout=2)
        except:
            process.kill()

if __name__ == "__main__":
    verify_payment_service()
