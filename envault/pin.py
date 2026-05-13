"""Pin management: lock a vault to a specific key version/fingerprint."""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

PIN_FILENAME = ".envault-pin"


def _get_pin_path(base_dir: str) -> str:
    return os.path.join(base_dir, PIN_FILENAME)


def _fingerprint(key: str) -> str:
    """Return a short SHA-256 fingerprint of the key."""
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def pin_key(key: str, vault_path: str, label: Optional[str] = None, base_dir: str = ".") -> dict:
    """Pin a vault file to the given key fingerprint.

    Returns the pin record that was written.
    """
    if not os.path.isfile(vault_path):
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    record = {
        "vault": os.path.abspath(vault_path),
        "fingerprint": _fingerprint(key),
        "label": label or "",
        "pinned_at": datetime.now(timezone.utc).isoformat(),
    }

    pin_path = _get_pin_path(base_dir)
    with open(pin_path, "w") as fh:
        json.dump(record, fh, indent=2)

    return record


def read_pin(base_dir: str = ".") -> Optional[dict]:
    """Read the current pin record, or None if no pin exists."""
    pin_path = _get_pin_path(base_dir)
    if not os.path.isfile(pin_path):
        return None
    with open(pin_path) as fh:
        return json.load(fh)


def verify_pin(key: str, base_dir: str = ".") -> bool:
    """Return True if the given key matches the stored fingerprint."""
    record = read_pin(base_dir)
    if record is None:
        return True  # no pin set — always passes
    return record["fingerprint"] == _fingerprint(key)


def remove_pin(base_dir: str = ".") -> bool:
    """Delete the pin file. Returns True if a file was removed."""
    pin_path = _get_pin_path(base_dir)
    if os.path.isfile(pin_path):
        os.remove(pin_path)
        return True
    return False
