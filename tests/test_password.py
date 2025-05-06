from app.core.security import hash_password, verify_password


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

    # Verify password verification works
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False