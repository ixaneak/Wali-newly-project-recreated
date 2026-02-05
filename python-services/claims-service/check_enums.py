import sqlalchemy as sa
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

target_types = ['coveragetype', 'policystatus', 'claimstatus', 'userrole', 'kycstatus', 'paymentfrequency']

with engine.connect() as conn:
    res = conn.execute(text("SELECT t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE n.nspname = 'public'"))
    actual_types = [row[0] for row in res]
    for tt in target_types:
        print(f"{tt}: {tt in actual_types}")
