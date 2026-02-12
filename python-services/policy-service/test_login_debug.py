import requests
import json
import sys

url = "http://localhost:8000/api/v1/pharmacy/auth/login"
headers = {"Content-Type": "application/json"}
payload = {"email": "pharmacie@wali.com", "password": "pharma1234"}

print(f"Testing URL: {url}")
try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("JSON Response:")
        print(json.dumps(data, indent=2))
    except:
        print("Raw Response Content:")
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
