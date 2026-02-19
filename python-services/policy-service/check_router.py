
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.routes import policies
    print("Successfully imported app.routes.policies")
    
    if hasattr(policies, "policies_router"):
        print("policies_router exists")
        router = policies.policies_router
        print(f"Prefix: {router.prefix}")
        print(f"Tags: {router.tags}")
        print(f"Routes: {len(router.routes)}")
        for r in router.routes:
            print(f" - {r.path} {r.methods}")
    else:
        print("policies_router NOT found in module")

except Exception as e:
    print(f"Error importing policies: {e}")
    import traceback
    traceback.print_exc()
