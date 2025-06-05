import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set TESTING environment variable before importing app
os.environ["TESTING"] = "true"

from app.core.database import Base, get_db
from app.main import app

# Add the project root to the Python path so pytest can find the app module
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Add command-line option to skip slow tests
def pytest_addoption(parser):
    parser.addoption("--skip-slow", action="store_true", default=False, help="Skip slow tests")


def pytest_configure(config):
    """Register slow marker and configure it to be skipped when --skip-slow is used."""
    # Register the 'slow' marker
    config.addinivalue_line("markers", "slow: marks tests as slow (skipped with --skip-slow)")

    # Skip slow tests if the --skip-slow flag is provided
    if config.getoption("--skip-slow"):
        # Add 'not slow' to the existing markexpr or set it if none exists
        markexpr = config.getoption("markexpr") or ""
        if markexpr:
            markexpr = f"{markexpr} and not slow"
        else:
            markexpr = "not slow"
        config.option.markexpr = markexpr


@pytest.fixture(scope="session")
def db_engine():
    """Create a clean test database before tests and drop it after"""
    # Create tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(db_engine):
    """Get a database session for each test"""
    connection = db_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    yield session

    # Rollback changes and close session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """Get a FastAPI test client"""

    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    # Clear dependency overrides
    app.dependency_overrides.clear()
