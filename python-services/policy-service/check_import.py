import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    print("Attempting to import app.models.policy...")
    import app.models.policy
    print(f"app.models.policy imported: {app.models.policy}")
    print(f"File: {app.models.policy.__file__}")
    
    print("Attempting to import CoverageSubscription from app.models.policy...")
    from app.models.policy import CoverageSubscription
    print("SUCCESS: CoverageSubscription imported")
except ImportError as e:
    print(f"FAILURE: {e}")
    if 'app.models.policy' in sys.modules:
        print(f"DIR: {dir(sys.modules['app.models.policy'])}")
    else:
        print("app.models.policy not in sys.modules")
except Exception as e:
    print(f"ERROR: {e}")
