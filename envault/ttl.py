"""TTL (time-to-live) support for vault secrets.

Allows marking a vault file with an expiry timestamp so that
consumers can detect stale secrets and prompt for re-locking.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_TTL_SUFFIX = ".ttl"


def _get_ttl_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(_TTL_SUFFIX)


@dataclass
class TTLEntry:
    vault: str
    expires_at: float  # Unix timestamp
    created_at: float

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def seconds_remaining(self) -> float:
        return max(0.0, self.expires_at - time.time())


def set_ttl(vault_path: str, seconds: int) -> TTLEntry:
    """Attach a TTL to *vault_path*. Returns the new TTLEntry."""
    if seconds <= 0:
        raise ValueError("TTL must be a positive number of seconds.")

    now = time.time()
    entry = TTLEntry(
        vault=os.path.abspath(vault_path),
        expires_at=now + seconds,
        created_at=now,
    )
    ttl_path = _get_ttl_path(vault_path)
    ttl_path.write_text(
        json.dumps(
            {
                "vault": entry.vault,
                "expires_at": entry.expires_at,
                "created_at": entry.created_at,
            },
            indent=2,
        )
    )
    return entry


def read_ttl(vault_path: str) -> Optional[TTLEntry]:
    """Return the TTLEntry for *vault_path*, or None if not set."""
    ttl_path = _get_ttl_path(vault_path)
    if not ttl_path.exists():
        return None
    data = json.loads(ttl_path.read_text())
    return TTLEntry(
        vault=data["vault"],
        expires_at=data["expires_at"],
        created_at=data["created_at"],
    )


def remove_ttl(vault_path: str) -> bool:
    """Remove the TTL file for *vault_path*. Returns True if it existed."""
    ttl_path = _get_ttl_path(vault_path)
    if ttl_path.exists():
        ttl_path.unlink()
        return True
    return False


def check_ttl(vault_path: str) -> Optional[TTLEntry]:
    """Return the TTLEntry if it exists AND is expired, else None."""
    entry = read_ttl(vault_path)
    if entry is not None and entry.is_expired():
        return entry
    return None
