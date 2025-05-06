import os
import pathlib

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

DB_FILENAME = os.getenv("DB_FILENAME", "dev.db")
DB_PATH = pathlib.Path(DB_FILENAME)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Create engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}, echo=False
)

# Session factory
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

# Declarative base
Base = declarative_base()


def get_db():
    """
    Get a database session for dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database file (if SQLite) and tables for all models imported.

    In a testing environment (signaled by TESTING env var or DB_FILENAME containing 'test'),
    this will also drop all existing tables first to ensure a clean state.
    """
    # Import models here so they register with Base.metadata before create_all
    from app import models  # noqa: F401

    is_testing_env = (
        os.getenv("TESTING") == "true" or "test" in DB_FILENAME.lower() or (DB_PATH and "test" in DB_PATH.name.lower())
    )

    if is_testing_env:
        Base.metadata.drop_all(bind=engine)

    if DATABASE_URL.startswith("sqlite"):
        if not DB_PATH.exists():
            # ensure parent directory
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
