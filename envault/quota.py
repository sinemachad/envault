"""Quota management — enforce limits on the number of keys stored in a vault."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DEFAULT_QUOTA = 100


def _get_quota_path(base_dir: str) -> Path:
    return Path(base_dir) / ".envault" / "quota.json"


def _load_quota(base_dir: str) -> dict:
    path = _get_quota_path(base_dir)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_quota(base_dir: str, data: dict) -> None:
    path = _get_quota_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


@dataclass
class QuotaEntry:
    vault: str
    limit: int
    current: int

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.current)

    @property
    def exceeded(self) -> bool:
        return self.current > self.limit

    def __repr__(self) -> str:
        return (
            f"QuotaEntry(vault={self.vault!r}, limit={self.limit}, "
            f"current={self.current}, remaining={self.remaining})"
        )


def set_quota(base_dir: str, vault: str, limit: int) -> QuotaEntry:
    """Set the maximum number of keys allowed for *vault*."""
    if limit < 1:
        raise ValueError("Quota limit must be a positive integer.")
    data = _load_quota(base_dir)
    data[vault] = {"limit": limit}
    _save_quota(base_dir, data)
    return QuotaEntry(vault=vault, limit=limit, current=0)


def get_quota(base_dir: str, vault: str) -> QuotaEntry:
    """Return the quota entry for *vault*, using the default if none is set."""
    from envault.vault import unlock  # local import to avoid circular deps

    data = _load_quota(base_dir)
    limit = data.get(vault, {}).get("limit", DEFAULT_QUOTA)
    return QuotaEntry(vault=vault, limit=limit, current=0)


def check_quota(base_dir: str, vault: str, key: str, current_keys: list[str]) -> QuotaEntry:
    """Raise *OverflowError* when adding *key* would exceed the vault quota."""
    data = _load_quota(base_dir)
    limit = data.get(vault, {}).get("limit", DEFAULT_QUOTA)
    current = len(current_keys)
    entry = QuotaEntry(vault=vault, limit=limit, current=current)
    if key not in current_keys and current >= limit:
        raise OverflowError(
            f"Quota exceeded for vault '{vault}': "
            f"limit is {limit}, currently at {current} keys."
        )
    return entry


def remove_quota(base_dir: str, vault: str) -> bool:
    """Remove the quota setting for *vault*. Returns True if a record existed."""
    data = _load_quota(base_dir)
    if vault not in data:
        return False
    del data[vault]
    _save_quota(base_dir, data)
    return True
