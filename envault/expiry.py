"""Key expiry tracking — record expiry dates for vault keys and check staleness."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_EXPIRY_FILE = ".envault_expiry.json"


def _get_expiry_path(base_dir: str) -> Path:
    return Path(base_dir) / _EXPIRY_FILE


def _load_expiry(base_dir: str) -> dict:
    path = _get_expiry_path(base_dir)
    if not path.exists():
        return {}
    with open(path) as fh:
        return json.load(fh)


def _save_expiry(base_dir: str, data: dict) -> None:
    path = _get_expiry_path(base_dir)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


@dataclass
class ExpiryEntry:
    vault: str
    expires_at: str  # ISO-8601 UTC
    note: str

    def is_expired(self) -> bool:
        expiry = datetime.fromisoformat(self.expires_at).replace(tzinfo=timezone.utc)
        return datetime.now(tz=timezone.utc) >= expiry

    def days_remaining(self) -> int:
        expiry = datetime.fromisoformat(self.expires_at).replace(tzinfo=timezone.utc)
        delta = expiry - datetime.now(tz=timezone.utc)
        return max(0, delta.days)

    def __repr__(self) -> str:
        status = "EXPIRED" if self.is_expired() else f"{self.days_remaining()}d remaining"
        return f"<ExpiryEntry vault={self.vault!r} expires_at={self.expires_at!r} [{status}]>"


def set_expiry(vault_path: str, expires_at: str, note: str = "", base_dir: Optional[str] = None) -> ExpiryEntry:
    """Record an expiry date for a vault file."""
    base_dir = base_dir or os.path.dirname(os.path.abspath(vault_path))
    # Validate the date string
    datetime.fromisoformat(expires_at)
    data = _load_expiry(base_dir)
    entry = {"vault": vault_path, "expires_at": expires_at, "note": note}
    data[vault_path] = entry
    _save_expiry(base_dir, data)
    return ExpiryEntry(**entry)


def get_expiry(vault_path: str, base_dir: Optional[str] = None) -> Optional[ExpiryEntry]:
    """Return the expiry entry for a vault, or None if not set."""
    base_dir = base_dir or os.path.dirname(os.path.abspath(vault_path))
    data = _load_expiry(base_dir)
    raw = data.get(vault_path)
    if raw is None:
        return None
    return ExpiryEntry(**raw)


def remove_expiry(vault_path: str, base_dir: Optional[str] = None) -> bool:
    """Remove the expiry entry for a vault. Returns True if it existed."""
    base_dir = base_dir or os.path.dirname(os.path.abspath(vault_path))
    data = _load_expiry(base_dir)
    if vault_path not in data:
        return False
    del data[vault_path]
    _save_expiry(base_dir, data)
    return True


def list_expiries(base_dir: str) -> list[ExpiryEntry]:
    """Return all expiry entries recorded under base_dir."""
    data = _load_expiry(base_dir)
    return [ExpiryEntry(**v) for v in data.values()]
