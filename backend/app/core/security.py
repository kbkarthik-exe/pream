import hashlib
import secrets

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from backend.app.core.config import settings

# OWASP Recommended Argon2id parameters with memory-constrained fallback
_is_test = getattr(settings, "ENVIRONMENT", "") == "test"
_hasher = PasswordHasher(
    time_cost=1 if _is_test else 2,
    memory_cost=19456 if _is_test else 65536,
    parallelism=1 if _is_test else 2,
    hash_len=32,
    type=Type.ID,
)
_fallback_hasher = PasswordHasher(
    time_cost=1,
    memory_cost=19456,
    parallelism=1,
    hash_len=32,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    """Hash password using Argon2id algorithm."""
    try:
        return _hasher.hash(password)
    except Exception:
        return _fallback_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against an Argon2id hash."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False


def generate_session_token() -> str:
    """Generate a high-entropy URL-safe session token (256 bits)."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Compute SHA-256 hash of a session token for secure DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
