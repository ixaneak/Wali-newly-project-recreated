
import requests
try:
    resp = requests.get("http://localhost:8000/", timeout=5)
    print(f"Status: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
