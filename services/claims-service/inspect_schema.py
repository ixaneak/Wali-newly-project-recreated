import sqlalchemy as sa
from sqlalchemy import create_engine, inspect
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

inspector = inspect(engine)

print("\n--- POLICIES TABLE ---")
if inspector.has_table("policies"):
    for col in inspector.get_columns("policies"):
        print(f"Column: {col['name']} ({col['type']})")
else:
    print("Table 'policies' not found")
