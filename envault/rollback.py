"""Rollback support: restore a vault to a previous history entry."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from envault.history import read_history
from envault.vault import lock, unlock


@dataclass
class RollbackResult:
    vault_path: str
    rolled_back_to: str          # action label of the target entry
    previous_action: str         # action label we rolled back from
    keys_restored: int

    def __repr__(self) -> str:   # pragma: no cover
        return (
            f"<RollbackResult vault={self.vault_path!r} "
            f"to={self.rolled_back_to!r} keys={self.keys_restored}>"
        )


def list_rollback_points(vault_path: str) -> list[dict]:
    """Return history entries that contain a snapshot usable for rollback."""
    return [
        entry for entry in read_history(vault_path)
        if entry.get("snapshot")
    ]


def rollback(vault_path: str, key: str, index: int = 0) -> RollbackResult:
    """
    Restore *vault_path* to the snapshot stored in history entry *index*
    (0 = most recent snapshot, 1 = second most recent, …).

    Raises IndexError if *index* is out of range.
    Raises ValueError if the target entry has no snapshot.
    """
    points = list_rollback_points(vault_path)
    if not points:
        raise ValueError(f"No rollback points found for {vault_path!r}")
    if index >= len(points):
        raise IndexError(
            f"Rollback index {index} out of range (have {len(points)} points)"
        )

    target = points[index]
    snapshot: dict = target["snapshot"]          # plain-text env dict

    # Determine the current action label before overwriting
    all_entries = read_history(vault_path)
    previous_action = all_entries[0]["action"] if all_entries else "unknown"

    # Re-encrypt and write vault
    lock(snapshot, vault_path, key)

    return RollbackResult(
        vault_path=vault_path,
        rolled_back_to=target["action"],
        previous_action=previous_action,
        keys_restored=len(snapshot),
    )
