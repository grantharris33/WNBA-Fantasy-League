import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import TransactionLog, User


def test_transaction_log_fields(db):
    """Test that the TransactionLog model has the fields required by Story-8."""
    # Create a test user
    user = User(email="test@example.com", hashed_password="hashed_password", is_admin=False)
    db.add(user)
    db.commit()

    # Create a transaction log with all fields
    log = TransactionLog(
        user_id=user.id,
        action="Test action",
        method="POST",
        path="/api/v1/test",
        patch='[{"op": "replace", "path": "/test", "value": "new value"}]',
    )
    db.add(log)
    db.commit()

    # Retrieve the log
    saved_log = db.query(TransactionLog).filter(TransactionLog.action == "Test action").first()

    # Verify fields
    assert saved_log is not None
    assert saved_log.user_id == user.id
    assert saved_log.action == "Test action"
    assert saved_log.method == "POST"
    assert saved_log.path == "/api/v1/test"
    assert saved_log.patch == '[{"op": "replace", "path": "/test", "value": "new value"}]'
    assert saved_log.timestamp is not None


def test_user_is_admin_field(db):
    """Test that the User model has the is_admin field."""
    # Create an admin user
    admin = User(email="admin@example.com", hashed_password="hashed_password", is_admin=True)
    db.add(admin)

    # Create a non-admin user
    user = User(email="user@example.com", hashed_password="hashed_password", is_admin=False)
    db.add(user)
    db.commit()

    # Retrieve the users
    saved_admin = db.query(User).filter(User.email == "admin@example.com").first()
    saved_user = db.query(User).filter(User.email == "user@example.com").first()

    # Verify fields
    assert saved_admin is not None
    assert saved_user is not None
    assert saved_admin.is_admin is True
    assert saved_user.is_admin is False
