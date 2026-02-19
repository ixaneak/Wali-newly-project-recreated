import sys
import os
import traceback

sys.path.append(os.getcwd())

try:
    print("Attempting to import app.routes.mfa...")
    from app.routes import mfa
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    traceback.print_exc()

try:
    print("\nAttempting to import app.core.secure_auth...")
    from app.core import secure_auth
    print("secure_auth import successful!")
    print(f"verify_token available? {'verify_token' in dir(secure_auth)}")
except Exception as e:
    print(f"secure_auth import failed: {e}")
    traceback.print_exc()
