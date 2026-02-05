import sqlalchemy as sa
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    res = conn.execute(text("SELECT conname FROM pg_constraint WHERE conrelid = 'claims'::regclass AND contype = 'f'"))
    fks = [row[0] for row in res]
    print("Foreign keys on claims table:")
    for fk in fks:
        print(f"  - {fk}")
    print(f"\nTotal: {len(fks)} foreign keys")
