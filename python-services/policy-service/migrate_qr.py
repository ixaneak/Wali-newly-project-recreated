import sqlite3
import os

DB_PATH = "./test.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(coverage_subscriptions)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "qr_token" not in columns:
            print("Adding qr_token column...")
            cursor.execute("ALTER TABLE coverage_subscriptions ADD COLUMN qr_token VARCHAR")
            cursor.execute("CREATE UNIQUE INDEX ix_coverage_subscriptions_qr_token ON coverage_subscriptions (qr_token)")
        else:
            print("qr_token already exists.")

        if "qr_expires_at" not in columns:
            print("Adding qr_expires_at column...")
            cursor.execute("ALTER TABLE coverage_subscriptions ADD COLUMN qr_expires_at DATETIME")
        else:
             print("qr_expires_at already exists.")

        if "verification_hash" not in columns:
            print("Adding verification_hash column...")
            cursor.execute("ALTER TABLE coverage_subscriptions ADD COLUMN verification_hash VARCHAR")
        else:
             print("verification_hash already exists.")
             
        conn.commit()
        print("Migration successful!")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
