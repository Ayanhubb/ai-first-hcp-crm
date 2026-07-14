"""Password hashing utilities (Argon2id)."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Argon2id with conservative production defaults (argon2-cffi recommendations).
_PASSWORD_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65_536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with Argon2id. Never store the plaintext."""
    _validate_password_length(plain_password)
    return _PASSWORD_HASHER.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Returns False on mismatch or malformed hash (no exception leakage).
    Constant-time relative to verify path provided by argon2-cffi.
    """
    if not plain_password or not password_hash:
        return False
    try:
        return _PASSWORD_HASHER.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True when the stored hash should be upgraded to current parameters."""
    try:
        return _PASSWORD_HASHER.check_needs_rehash(password_hash)
    except (InvalidHashError, VerificationError):
        return True


def _validate_password_length(plain_password: str) -> None:
    length = len(plain_password)
    if length < MIN_PASSWORD_LENGTH or length > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password length must be between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH}"
        )
