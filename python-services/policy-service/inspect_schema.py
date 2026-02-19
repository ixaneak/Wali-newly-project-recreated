import sys
import os
import sqlalchemy
from sqlalchemy import text, inspect

sys.path.append(os.getcwd())
from app.core.database import engine

def inspect_db():
    print(f"Database URL: {engine.url}")
    inspector = inspect(engine)
    columns = inspector.get_columns('users')
    print("Columns in 'users' table:")
    for c in columns:
        print(f" - {c['name']} ({c['type']})")

if __name__ == "__main__":
    inspect_db()
