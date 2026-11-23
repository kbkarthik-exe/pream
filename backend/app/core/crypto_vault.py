"""Cryptographic Vault for securely storing user third-party cloud API keys.

SECURITY RULES:
- Raw API keys are NEVER stored in plaintext in the database.
- Raw API keys are NEVER returned to frontend clients or logs.
- Decrypted keys exist in memory only during the lifetime of an outbound HTTPS request.
- Uses authenticated encryption with key derivation from application master secret + user context.
"""

import base64
import hashlib
import hmac
import os

from backend.app.core.config import settings


def _derive_user_key(user_id: int) -> bytes:
    """Derives a user-specific encryption key from application secret and user context."""
    master = settings.SECRET_KEY.encode("utf-8")
    salt = f"aicf_cloud_vault_v1_user_{user_id}".encode()
    return hashlib.pbkdf2_hmac("sha256", master, salt, iterations=100_000, dklen=32)


def encrypt_api_key(plain_key: str, user_id: int) -> str:
    """Encrypts a plain API key string with authenticated encryption (Encrypt-then-MAC).

    Output format: base64(iv[16] + ciphertext + mac[32])
    """
    if not plain_key:
        return ""

    key_bytes = _derive_user_key(user_id)
    iv = os.urandom(16)
    data = plain_key.encode("utf-8")

    # Keystream generation via HMAC-SHA256 expansion
    keystream = bytearray()
    counter = 0
    while len(keystream) < len(data):
        block = hmac.digest(key_bytes, iv + counter.to_bytes(4, "big"), hashlib.sha256)
        keystream.extend(block)
        counter += 1

    ciphertext = bytes(a ^ b for a, b in zip(data, keystream[: len(data)]))
    # Authenticate IV + Ciphertext
    mac = hmac.digest(key_bytes, iv + ciphertext, hashlib.sha256)

    payload = iv + ciphertext + mac
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt_api_key(encrypted_token: str, user_id: int) -> str:
    """Decrypts and verifies an encrypted API key string.

    Raises ValueError if token is tampered with or corrupted.
    """
    if not encrypted_token:
        return ""

    try:
        raw = base64.urlsafe_b64decode(encrypted_token.encode("ascii"))
    except Exception as exc:
        raise ValueError(f"Malformed encrypted token: {exc}") from exc

    if len(raw) < 16 + 32:
        raise ValueError("Invalid encrypted token length.")

    iv = raw[:16]
    ciphertext = raw[16:-32]
    expected_mac = raw[-32:]

    key_bytes = _derive_user_key(user_id)
    actual_mac = hmac.digest(key_bytes, iv + ciphertext, hashlib.sha256)

    if not hmac.compare_digest(expected_mac, actual_mac):
        raise ValueError("Integrity check failed: Encrypted token has been tampered with or key mismatch.")

    # Reconstruct keystream
    keystream = bytearray()
    counter = 0
    while len(keystream) < len(ciphertext):
        block = hmac.digest(key_bytes, iv + counter.to_bytes(4, "big"), hashlib.sha256)
        keystream.extend(block)
        counter += 1

    plain_bytes = bytes(a ^ b for a, b in zip(ciphertext, keystream[: len(ciphertext)]))
    return plain_bytes.decode("utf-8")


def mask_api_key(key: str | None) -> str:
    """Masks an API key for safe public representation without exposing secrets.

    Example: "live_secret_1234567890abcdef" -> "live_...cdef"
    """
    if not key:
        return "NOT_CONFIGURED"

    clean = key.strip()
    if len(clean) <= 8:
        return "••••••••"

    prefix = clean[:4]
    suffix = clean[-4:]
    return f"{prefix}••••••••{suffix}"
