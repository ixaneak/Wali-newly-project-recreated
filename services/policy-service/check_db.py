import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.environ.get("DATABASE_URL")
print(f"Connecting to: {url}")

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"Success! Result: {result.fetchone()}")
        
        # Check privileges
        try:
            conn.execute(text("CREATE TABLE test_table (id serial PRIMARY KEY)"))
            print("Create table success")
            conn.execute(text("DROP TABLE test_table"))
            print("Drop table success")
        except Exception as e:
            print(f"Permission error: {e}")

except Exception as e:
    print(f"Connection failed: {e}")
