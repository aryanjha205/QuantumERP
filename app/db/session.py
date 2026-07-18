from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# For Neon DB (PostgreSQL with SSL) on serverless environments
connect_args = {}
db_uri = settings.SQLALCHEMY_DATABASE_URI
if "sslmode=require" in db_uri or "neon.tech" in db_uri:
    connect_args = {"sslmode": "require"}

engine = create_engine(
    db_uri,
    pool_pre_ping=True,
    pool_size=1,         # Minimal pool for serverless
    max_overflow=0,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

