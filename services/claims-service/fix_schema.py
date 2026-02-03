import sqlalchemy as sa
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Add column if not exists
    conn.execute(text("ALTER TABLE policies ADD COLUMN IF NOT EXISTS coverage_type coveragetype"))
    conn.commit()
    print("Column added and committed!")
    
    # Verify
    res = conn.execute(text("SELECT * FROM policies LIMIT 0"))
    print("Columns:", list(res.keys()))
    print("coverage_type exists:", 'coverage_type' in res.keys())
