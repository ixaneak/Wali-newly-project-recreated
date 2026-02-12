import sqlite3
import os

DB_PATH = "test.db"

if not os.path.exists(DB_PATH):
    print(f"Database {DB_PATH} not found.")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def check_table(table_name):
    exists = cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone()
    if exists:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"✅ {table_name} exists (Rows: {count})")
        return True
    else:
        print(f"❌ {table_name} does NOT exist")
        return False

print("--- Checking Claims Service SaaS Tables ---")
check_table("incident_reports")

print("\n--- Checking Legacy Insurance Tables (Should be GONE) ---")
if check_table("claims"):
    print("⚠️ WARNING: Legacy 'claims' table still exists!")
else:
    print("✅ CLEAN: 'claims' table is gone.")
