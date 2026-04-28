"""Core encryption/decryption module for envault using Fernet symmetric encryption."""

import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_SIZE = 16
ITERATIONS = 390_000


def generate_key() -> str:
    """Generate a new random Fernet key, returned as a URL-safe base64 string."""
    return Fernet.generate_key().decode()


def derive_key(passphrase: str, salt: bytes | None = None) -> tuple[str, bytes]:
    """Derive a Fernet key from a passphrase using PBKDF2-HMAC-SHA256.

    Returns:
        (key_str, salt) — the derived key and the salt used.
    """
    if salt is None:
        salt = os.urandom(SALT_SIZE)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    raw_key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return raw_key.decode(), salt


def encrypt(plaintext: str, key: str) -> bytes:
    """Encrypt a plaintext string with the given Fernet key.

    Args:
        plaintext: The secret content to encrypt.
        key: A Fernet-compatible key string.

    Returns:
        Encrypted bytes (Fernet token).
    """
    f = Fernet(key.encode())
    return f.encrypt(plaintext.encode())


def decrypt(token: bytes, key: str) -> str:
    """Decrypt a Fernet token with the given key.

    Args:
        token: Encrypted bytes produced by `encrypt`.
        key: A Fernet-compatible key string.

    Returns:
        The original plaintext string.

    Raises:
        ValueError: If the key is invalid or the token is tampered.
    """
    try:
        f = Fernet(key.encode())
        return f.decrypt(token).decode()
    except (InvalidToken, Exception) as exc:
        raise ValueError("Decryption failed: invalid key or corrupted data.") from exc
