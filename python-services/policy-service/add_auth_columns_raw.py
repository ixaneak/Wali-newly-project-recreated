import sys
import os
import sqlalchemy
from sqlalchemy import text, inspect

# Add current directory to path
sys.path.append(os.getcwd())

from app.core.database import engine

def add_columns_safe():
    print(f"Using database: {engine.url}")
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('users')]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            if 'email' not in columns:
                print("Adding email column...")
                # SQLite doesn't support adding UNIQUE constraint in ADD COLUMN usually
                # But let's try simple ADD COLUMN first
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
                print("Adding unique index on email...")
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
            else:
                print("email column already exists.")

            if 'password_hash' not in columns:
                print("Adding password_hash column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
            else:
                print("password_hash column already exists.")
                
            trans.commit()
            print("Schema update completed successfully.")
        except Exception as e:
            trans.rollback()
            print(f"Error updating schema: {e}")

if __name__ == "__main__":
    add_columns_safe()
