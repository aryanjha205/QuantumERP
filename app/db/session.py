from threading import Lock

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

# Do not connect to the database while Vercel imports the function. A failed
# connection at import time turns even /health into FUNCTION_INVOCATION_FAILED.
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
_initialized = False
_initialization_lock = Lock()


def initialize_database() -> None:
    """Connect and create missing tables on the first database request."""
    global _initialized
    if _initialized:
        return

    with _initialization_lock:
        if _initialized:
            return

        db_uri = settings.SQLALCHEMY_DATABASE_URI
        if not db_uri:
            raise RuntimeError("SQLALCHEMY_DATABASE_URI is not configured")

        connect_args = {}
        if "sslmode=require" in db_uri or "neon.tech" in db_uri:
            connect_args = {"sslmode": "require"}

        engine = create_engine(
            db_uri,
            pool_pre_ping=True,
            poolclass=NullPool,
            connect_args=connect_args,
        )
        Base.metadata.create_all(bind=engine)
        SessionLocal.configure(bind=engine)
        _initialized = True
