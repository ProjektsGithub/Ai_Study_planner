"""
Tests for security utilities
"""
import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_password_strength,
)


def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword123"
    hashed = get_password_hash(password)
    
    # Hash should be different from original
    assert hashed != password
    
    # Verification should succeed
    assert verify_password(password, hashed) is True
    
    # Wrong password should fail
    assert verify_password("WrongPassword", hashed) is False


def test_create_and_decode_access_token():
    """Test access token creation and decoding"""
    data = {"sub": "123"}
    token = create_access_token(data)
    
    # Token should be a string
    assert isinstance(token, str)
    
    # Decode token
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_and_decode_refresh_token():
    """Test refresh token creation and decoding"""
    data = {"sub": "123"}
    token = create_refresh_token(data)
    
    # Token should be a string
    assert isinstance(token, str)
    
    # Decode token
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_invalid_token():
    """Test decoding invalid token"""
    invalid_token = "invalid.token.here"
    payload = decode_token(invalid_token)
    assert payload is None


def test_validate_password_strength_valid():
    """Test password strength validation with valid passwords"""
    valid_passwords = [
        "Test1234",
        "MyPassword123",
        "Secure@Pass1",
        "ComplexP@ssw0rd",
    ]
    
    for password in valid_passwords:
        is_valid, error = validate_password_strength(password)
        assert is_valid is True
        assert error is None


def test_validate_password_strength_too_short():
    """Test password validation with too short password"""
    is_valid, error = validate_password_strength("Test12")
    assert is_valid is False
    assert "8 characters" in error


def test_validate_password_strength_no_uppercase():
    """Test password validation without uppercase"""
    is_valid, error = validate_password_strength("test1234")
    assert is_valid is False
    assert "uppercase" in error.lower()


def test_validate_password_strength_no_lowercase():
    """Test password validation without lowercase"""
    is_valid, error = validate_password_strength("TEST1234")
    assert is_valid is False
    assert "lowercase" in error.lower()


def test_validate_password_strength_no_digit():
    """Test password validation without digit"""
    is_valid, error = validate_password_strength("TestTest")
    assert is_valid is False
    assert "digit" in error.lower()
