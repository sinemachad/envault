"""Key rotation support for envault vaults."""

import json
from pathlib import Path
from typing import Optional

from .crypto import generate_key, encrypt, decrypt
from .vault import parse_env, serialize_env
from .audit import record_event


def rotate_key(
    vault_path: str,
    old_key: str,
    new_key: Optional[str] = None,
) -> str:
    """Re-encrypt a vault file with a new key.

    Decrypts the vault using *old_key*, then re-encrypts the plaintext
    with *new_key* (auto-generated when omitted).  The vault file is
    updated in-place and the new key is returned.

    Args:
        vault_path: Path to the encrypted ``.env.vault`` file.
        old_key: Base-64 encoded key currently protecting the vault.
        new_key: Replacement key.  A fresh key is generated when ``None``.

    Returns:
        The new key (base-64 encoded string).

    Raises:
        ValueError: If the vault cannot be decrypted with *old_key*.
        FileNotFoundError: If *vault_path* does not exist.
    """
    path = Path(vault_path)
    if not path.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")

    ciphertext = path.read_text(encoding="utf-8").strip()

    try:
        plaintext = decrypt(ciphertext, old_key)
    except Exception as exc:
        raise ValueError(f"Failed to decrypt vault with provided key: {exc}") from exc

    if new_key is None:
        new_key = generate_key()

    new_ciphertext = encrypt(plaintext, new_key)
    path.write_text(new_ciphertext + "\n", encoding="utf-8")

    record_event(
        "rotate",
        {"vault": str(path.resolve()), "rotated": True},
    )

    return new_key


def rotate_env_key(
    env_path: str,
    old_key: str,
    new_key: Optional[str] = None,
) -> str:
    """Convenience wrapper: rotate the key for a plain ``.env`` vault pair.

    The companion ``<env_path>.vault`` file is rotated; the plaintext
    ``.env`` file is never written.
    """
    vault_path = env_path if env_path.endswith(".vault") else env_path + ".vault"
    return rotate_key(vault_path, old_key, new_key)
