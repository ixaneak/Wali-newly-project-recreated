import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.policy import User
from app.core.secure_auth import verify_password, hash_password

def check_admin():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@wali.com").first()
        if not user:
            print("User admin@wali.com NOT FOUND.")
            return

        print(f"User found: {user.email}, Role: {user.role}")
        print(f"Hash in DB: {user.password_hash}")
        
        is_valid = verify_password("admin123", user.password_hash)
        print(f"verify_password('admin123', hash) -> {is_valid}")
        
        if not is_valid:
            print("Password verification FAILED.")
            # Debug: generate new hash and compare (visual check)
            new_hash = hash_password("admin123")
            print(f"New hash for 'admin123': {new_hash}")
        else:
            print("Password verification SUCCESSFUL.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_admin()
