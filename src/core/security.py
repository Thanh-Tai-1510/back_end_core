"""Password hashing (bcrypt) and JWT helpers. Building blocks only; no auth routes here."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import anyio
import bcrypt
from jose import JWTError, jwt

from core.config import settings

BCRYPT_ROUNDS = 12
# bcrypt only uses the first 72 bytes. bcrypt 4.x truncated silently, 5.x raises instead, so
# truncate here: hashes made either way keep verifying, whatever version is installed.
_BCRYPT_MAX_BYTES = 72


def _password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        # Malformed stored hash.
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


# bcrypt takes ~250ms of CPU; run it in a worker thread so the event loop keeps serving requests.
async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    return await anyio.to_thread.run_sync(verify_password, plain_password, hashed_password)


async def get_password_hash_async(password: str) -> str:
    return await anyio.to_thread.run_sync(get_password_hash, password)


def _secret(secret_key: str | None) -> str:
    key = secret_key or settings.JWT_SECRET_KEY
    if not key:
        raise RuntimeError("JWT_SECRET_KEY is not configured")
    return key


def create_access_token(
    subject: str | int,
    *,
    secret_key: str | None = None,
    algorithm: str | None = None,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    minutes = expires_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    payload: dict[str, Any] = {"sub": str(subject), "exp": datetime.now(UTC) + timedelta(minutes=minutes)}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _secret(secret_key), algorithm=algorithm or settings.JWT_ALGORITHM)


def decode_access_token(
    token: str,
    *,
    secret_key: str | None = None,
    algorithm: str | None = None,
) -> dict[str, Any] | None:
    """Claims of a valid, unexpired token, or None."""
    try:
        return jwt.decode(token, _secret(secret_key), algorithms=[algorithm or settings.JWT_ALGORITHM])
    except JWTError:
        return None


def generate_token(nbytes: int = 48) -> str:
    """Random URL-safe token (refresh tokens, reset links, API keys)."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """SHA-256 hex digest, for storing opaque tokens without keeping the token itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
