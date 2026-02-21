import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine, Base
from app.models.policy import User, UserRole, KYCStatus
from app.core.secure_auth import hash_password
import uuid

from app.core.config import get_settings

def create_admin_user():
    settings = get_settings()
    print(f"DEBUG: create_admin_user using DB: {settings.database_url}")
    db = SessionLocal()
    try:
        email = "admin@wali.ci"
        phone = "+2250700000000"
        
        # Check if exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
             user = db.query(User).filter(User.phone == phone).first()
             
        if user:
            print(f"Updating existing admin user: {user.id}")
            user.role = UserRole.ADMIN
            user.email = email
            user.password_hash = hash_password("admin123")
            user.name = "Super Admin"
        else:
            print("Creating new admin user")
            user = User(
                id=str(uuid.uuid4()),
                phone=phone,
                email=email,
                role=UserRole.ADMIN,
                name="Super Admin",
                kyc_status=KYCStatus.VERIFIED,
                password_hash=hash_password("admin123"),
                region="Abidjan"
            )
            db.add(user)
            
        db.commit()
        print("Admin user created/updated successfully.")
        print(f"Email: {email}")
        print(f"Password: admin123")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
