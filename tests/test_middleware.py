import pytest
from fastapi import Depends, FastAPI, Request, Response
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.deps import get_current_user
from app.core.middleware import ChangeLogMiddleware
from app.models import TransactionLog, User


def test_middleware_skips_get_requests(db):
    """Test that the middleware does not log GET requests for the specified methods."""
    # Create a middleware instance directly
    middleware = ChangeLogMiddleware(None)

    # Verify that GET is not in the mutating methods
    assert "GET" not in middleware.mutating_methods
    assert "POST" in middleware.mutating_methods
    assert "PUT" in middleware.mutating_methods
    assert "DELETE" in middleware.mutating_methods
    assert "PATCH" in middleware.mutating_methods


def test_middleware_serialization_utils():
    """Test the serialization and diff utility functions."""
    from app.core.middleware import compute_json_patch, serialize_model

    # Create test data
    before = {"name": "John", "age": 30}
    after = {"name": "John", "age": 31}

    # Test patch generation
    patch = compute_json_patch(before, after)
    assert patch is not None
    assert isinstance(patch, str)
    assert "31" in patch  # The new age should be in the patch


def test_transaction_log_model(db):
    """Test that the TransactionLog model has the expected fields."""
    # Create a TransactionLog instance with the new fields
    log = TransactionLog(
        user_id=None,
        action="TEST",
        method="POST",
        path="/test/path",
        patch='[{"op": "replace", "path": "/age", "value": 31}]',
    )

    # Add and commit to the database
    db.add(log)
    db.commit()

    # Retrieve the log
    saved_log = db.query(TransactionLog).filter(TransactionLog.action == "TEST").first()

    # Verify fields
    assert saved_log is not None
    assert saved_log.method == "POST"
    assert saved_log.path == "/test/path"
    assert saved_log.patch == '[{"op": "replace", "path": "/age", "value": 31}]'
