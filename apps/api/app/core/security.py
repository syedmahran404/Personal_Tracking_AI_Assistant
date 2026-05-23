"""Security primitives: password hashing + JWT issuance/verification.

- Passwords: bcrypt via passlib.
- Tokens: HS256 JWTs (access + refresh) with `typ` claim to prevent confusion.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _now() -> datetime:
    return datetime.now(UTC)


def create_token(
    subject: str | uuid.UUID,
    token_type: TokenType,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT.

    Args:
        subject: User id (string or UUID).
        token_type: 'access' or 'refresh' — written to `typ` claim.
        extra_claims: optional additional claims (e.g. {"role": "admin"}).
    """
    now = _now()
    if token_type == "access":
        exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "typ": token_type,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    """Decode + verify a JWT. Raises JWTError on any failure."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if expected_type is not None and payload.get("typ") != expected_type:
        raise JWTError(f"Invalid token type, expected {expected_type}")
    return payload


__all__ = [
    "JWTError",
    "create_token",
    "decode_token",
    "hash_password",
    "verify_password",
]
