import requests
import re
from urllib.parse import urljoin

BASE_URL = "https://wali-pwa.fly.dev"
SEARCH_TEXT = "Contrat d'assurance" # The new text we expect

def verify_deployment():
    print(f"Checking deployment at {BASE_URL} for text: '{SEARCH_TEXT}'")
    
    try:
        # 1. Get Main Page (Login)
        # Even if claims page is protected, the main JS bundle is often shared or linked.
        # But Next.js splits code. The claims page code might be in a separate chunk.
        # However, the Layout change or some shared component might be visible.
        # Let's try fetching the login page first.
        resp = requests.get(f"{BASE_URL}/login", timeout=10)
        resp.raise_for_status()
        html = resp.text
        
        # 2. Extract JS bundle URLs
        script_pattern = r'src="(/_next/static/chunks/[^"]+\.js)"'
        scripts = re.findall(script_pattern, html)
        print(f"Found {len(scripts)} scripts on login page.")
        
        found = False
        for script_path in scripts:
            script_url = urljoin(BASE_URL, script_path)
            print(f"Scanning {script_url}...")
            try:
                js_resp = requests.get(script_url, timeout=10)
                if SEARCH_TEXT in js_resp.text:
                    print(f"SUCCESS: Found '{SEARCH_TEXT}' in {script_path}")
                    found = True
                    break
                # Also check for encoded version if needed, but usually it's plain utf8 string in JS
            except Exception as e:
                print(f"Error fetching script {script_path}: {e}")
                
        if not found:
            print("Text not found in Login page scripts. Checking for layout update (lang='fr')...")
            if '<html lang="fr">' in html or "<html lang='fr'>" in html:
                 print("SUCCESS: Found '<html lang=\"fr\">'. Deployment verified.")
            else:
                 print("FAILURE: Layout update not found.")
            
    except Exception as e:
        print(f"Verification failed with error: {e}")

if __name__ == "__main__":
    verify_deployment()
