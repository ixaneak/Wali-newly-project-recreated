import requests
import json
import time

url = "http://localhost:8001/api/v1/policies/my-policies"
headers = {
    "Authorization": "Bearer mock-custom-token-backend"
}

try:
    with open("api_test_output.txt", "w") as f:
        f.write(f"Fetching {url}...\n")
        try:
            response = requests.get(url, headers=headers)
            f.write(f"Status: {response.status_code}\n")
            try:
                data = response.json()
                f.write(f"Error: {json.dumps(data)}\n")
            except:
                f.write(f"Raw Response: {response.text}\n")
        except Exception as e:
            f.write(f"Request Exception: {str(e)}\n")
except Exception as e:
    print(f"File Exception: {e}")
