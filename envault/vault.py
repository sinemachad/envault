"""Vault module for reading, writing, and managing encrypted .env files."""

import os
import json
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import encrypt, decrypt, derive_key

DEFAULT_VAULT_FILE = ".env.vault"
DEFAULT_ENV_FILE = ".env"


def parse_env(content: str) -> Dict[str, str]:
    """Parse .env file content into a dictionary."""
    result = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def serialize_env(data: Dict[str, str]) -> str:
    """Serialize a dictionary to .env file content."""
    lines = []
    for key, value in sorted(data.items()):
        if any(c in value for c in (" ", "#", "\n", '"')):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def lock(
    key: str,
    env_path: str = DEFAULT_ENV_FILE,
    vault_path: str = DEFAULT_VAULT_FILE,
    password: Optional[str] = None,
) -> str:
    """Encrypt a .env file and write to a vault file. Returns vault path."""
    env_file = Path(env_path)
    if not env_file.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    raw = env_file.read_text(encoding="utf-8")
    derived = derive_key(key, password) if password else key
    token = encrypt(raw, derived)

    vault = {"version": 1, "token": token}
    Path(vault_path).write_text(json.dumps(vault, indent=2), encoding="utf-8")
    return vault_path


def unlock(
    key: str,
    vault_path: str = DEFAULT_VAULT_FILE,
    env_path: str = DEFAULT_ENV_FILE,
    password: Optional[str] = None,
) -> Dict[str, str]:
    """Decrypt a vault file and write to a .env file. Returns parsed env dict."""
    vault_file = Path(vault_path)
    if not vault_file.exists():
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    vault = json.loads(vault_file.read_text(encoding="utf-8"))
    token = vault.get("token")
    if not token:
        raise ValueError("Invalid vault file: missing token")

    derived = derive_key(key, password) if password else key
    raw = decrypt(token, derived)

    Path(env_path).write_text(raw, encoding="utf-8")
    return parse_env(raw)
