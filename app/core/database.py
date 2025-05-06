from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
import pathlib
import os

DB_FILENAME = os.getenv("DB_FILENAME", "dev.db")
DB_PATH = pathlib.Path(DB_FILENAME)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

# Session factory
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

# Declarative base
Base = declarative_base()


def init_db() -> None:
    """Create database file (if SQLite) and tables for all models imported."""
    # Import models here so they register with Base.metadata before create_all
    from app import models  # noqa: F401

    if DATABASE_URL.startswith("sqlite"):
        if not DB_PATH.exists():
            # ensure parent directory
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)