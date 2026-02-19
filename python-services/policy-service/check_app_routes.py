
import sys
import os

sys.path.append(os.getcwd())

try:
    from app.main import app
    print("\n--- APP ROUTES (FILTERED) ---")
    found = False
    for r in app.routes:
        if hasattr(r, "path"):
            if "policies" in r.path or "my-policies" in r.path:
                print(f"FOUND: {r.path} [{r.methods}]")
                found = True
    if not found:
        print("NOT FOUND: my-policies")
except Exception as e:
    print(f"Error importing app: {e}")
