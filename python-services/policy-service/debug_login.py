import sys
import os
import traceback
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.policy import User, UserRole

def debug_role():
    try:
        print("Starting role debug...", flush=True)
        db = SessionLocal()
        user = db.query(User).filter(User.email == "admin@wali.com").first()
        
        if not user:
            print("User NOT FOUND.", flush=True)
            return
            
        print(f"User Role: {user.role}", flush=True)
        print(f"User Role Type: {type(user.role)}", flush=True)
        print(f"UserRole.ADMIN: {UserRole.ADMIN}", flush=True)
        print(f"UserRole.ADMIN Type: {type(UserRole.ADMIN)}", flush=True)
        
        comparison = (user.role == UserRole.ADMIN)
        print(f"user.role == UserRole.ADMIN: {comparison}", flush=True)
        
        comparison_str = (str(user.role) == "admin")
        print(f"str(user.role) == 'admin': {comparison_str}", flush=True)
        
        db.close()
        
    except Exception as e:
        print(f"Exception: {e}", flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    debug_role()
