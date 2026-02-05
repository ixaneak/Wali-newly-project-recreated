import sqlalchemy as sa
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'policies'"))
    cols = [row[0] for row in res]
    print(", ".join(cols))
