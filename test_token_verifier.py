"""Unit tests for TokenVerifier — no FastAPI dependency.

Run: uv run python test_token_verifier.py
"""
from datetime import timedelta, datetime, timezone

import jwt

from app.core.security import TokenVerifier


def make_config():
    return type("FakeConfig", (), {
        "jwt_secret_key": "test-secret-key-for-unit-tests",
        "jwt_algorithm": "HS256",
    })()


def test_verify_valid_token_returns_claims():
    v = TokenVerifier(make_config())
    now = datetime.now(timezone.utc)
    token = jwt.encode({
        "sub": "testuser", "name": "Test User", "role": "payrollprocess",
        "exp": now + timedelta(hours=1), "iat": now, "type": "access_token",
    }, v.config.jwt_secret_key, algorithm=v.config.jwt_algorithm)
    claims = v.verify(token)
    assert claims["sub"] == "testuser"
    assert claims["role"] == "payrollprocess"


def test_expired_token_raises():
    v = TokenVerifier(make_config())
    now = datetime.now(timezone.utc)
    token = jwt.encode({
        "sub": "u", "exp": now - timedelta(hours=1),
        "iat": now - timedelta(hours=2), "type": "access_token",
    }, v.config.jwt_secret_key, algorithm=v.config.jwt_algorithm)
    try:
        v.verify(token)
        assert False, "should have raised"
    except jwt.ExpiredSignatureError:
        pass


def test_bad_signature_raises():
    v = TokenVerifier(make_config())
    now = datetime.now(timezone.utc)
    token = jwt.encode({
        "sub": "u", "exp": now + timedelta(hours=1),
        "iat": now, "type": "access_token",
    }, "wrong-key", algorithm="HS256")
    try:
        v.verify(token)
        assert False, "should have raised"
    except jwt.InvalidSignatureError:
        pass


def test_malformed_token_raises():
    v = TokenVerifier(make_config())
    try:
        v.verify("not-a-valid-jwt")
        assert False, "should have raised"
    except jwt.DecodeError:
        pass


if __name__ == "__main__":
    tests = [
        test_verify_valid_token_returns_claims,
        test_expired_token_raises,
        test_bad_signature_raises,
        test_malformed_token_raises,
    ]
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
    print("\nAll TokenVerifier unit tests passed!")
