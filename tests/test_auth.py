import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.main import app
from app.models import User


@pytest.fixture
def test_user(db: Session):
    """Create a test user in the database"""
    hashed_password = hash_password("testpassword")
    user = User(email="test@example.com", hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_password_hashing():
    """Test that password hashing is working correctly"""
    # Original password
    password = "mysecretpassword"

    # Hash the password
    hashed = hash_password(password)

    # Verify the hash is different from the original password
    assert hashed != password

    # Verify the hash is not reversible (we don't check the value directly,
    # but ensure it has the bcrypt format)
    assert hashed.startswith("$2b$")


def test_token_endpoint(client: TestClient, test_user):
    """Test token generation endpoint"""
    # Login with correct credentials
    response = client.post("/api/v1/token", data={"username": "test@example.com", "password": "testpassword"})

    # Check response
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Login with incorrect password
    response = client.post("/api/v1/token", data={"username": "test@example.com", "password": "wrongpassword"})

    # Should fail with 401
    assert response.status_code == 401


def test_protected_endpoint(client: TestClient, test_user):
    """Test protected endpoint access"""
    # First get a token
    response = client.post("/api/v1/token", data={"username": "test@example.com", "password": "testpassword"})

    token = response.json()["access_token"]

    # Access protected endpoint with token
    response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    # Should succeed
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "test@example.com"

    # Access without token
    response = client.get("/api/v1/me")

    # Should fail with 401
    assert response.status_code == 401

    # Access with invalid token
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer invalidtoken"})

    # Should fail with 401
    assert response.status_code == 401
