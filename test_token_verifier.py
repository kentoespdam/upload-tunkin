"""
Unit tests for TokenVerifier — no FastAPI dependency.
Tests: valid token, expired token, bad signature, malformed token.
"""
from datetime import timedelta, datetime, timezone
from unittest.mock import patch

import jwt
import pytest

from app.core.security import TokenVerifier


@pytest.fixture
def verifier():
    config = type("FakeConfig", (), {
        "jwt_secret_key": "test-secret-key-for-unit-tests",
        "jwt_algorithm": "HS256",
    })()
    return TokenVerifier(config)


@pytest.fixture
def valid_token(verifier):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "testuser",
        "name": "Test User",
        "role": "payrollprocess",
        "exp": now + timedelta(hours=1),
        "iat": now,
        "type": "access_token",
    }
    return jwt.encode(payload, verifier.config.jwt_secret_key, algorithm=verifier.config.jwt_algorithm)


class TestTokenVerifier:
    def test_verify_valid_token_returns_claims(self, verifier, valid_token):
        """Valid token → returns decoded claims."""
        claims = verifier.verify(valid_token)
        assert claims["sub"] == "testuser"
        assert claims["name"] == "Test User"
        assert claims["role"] == "payrollprocess"
        assert claims["type"] == "access_token"

    def test_verify_expired_token_raises(self, verifier):
        """Expired token → ExpiredSignatureError."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "testuser",
            "exp": now - timedelta(hours=1),  # already expired
            "iat": now - timedelta(hours=2),
            "type": "access_token",
        }
        token = jwt.encode(payload, verifier.config.jwt_secret_key, algorithm=verifier.config.jwt_algorithm)
        with pytest.raises(jwt.ExpiredSignatureError):
            verifier.verify(token)

    def test_verify_bad_signature_raises(self):
        """Wrong secret → InvalidSignatureError."""
        config = type("FakeConfig", (), {
            "jwt_secret_key": "correct-key",
            "jwt_algorithm": "HS256",
        })()
        wrong_verifier = TokenVerifier(config)

        now = datetime.now(timezone.utc)
        payload = {
            "sub": "testuser",
            "exp": now + timedelta(hours=1),
            "iat": now,
            "type": "access_token",
        }
        # Sign with different key
        token = jwt.encode(payload, "wrong-key", algorithm="HS256")
        with pytest.raises(jwt.InvalidSignatureError):
            wrong_verifier.verify(token)

    def test_verify_malformed_token_raises(self, verifier):
        """Garbage string → DecodeError."""
        with pytest.raises(jwt.DecodeError):
            verifier.verify("this.is.not.a.jwt")
