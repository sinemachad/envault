"""Track a per-vault change history (lock/unlock/rotate events)."""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

HISTORY_FILENAME = ".envault_history.json"
_MAX_ENTRIES = 500


def _get_history_path(vault_path: str) -> str:
    """Return the history file path co-located with *vault_path*."""
    directory = os.path.dirname(os.path.abspath(vault_path))
    return os.path.join(directory, HISTORY_FILENAME)


def _load_history(history_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(history_path):
        return []
    with open(history_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_history(history_path: str, entries: List[Dict[str, Any]]) -> None:
    with open(history_path, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2)


def record_change(
    vault_path: str,
    action: str,
    actor: Optional[str] = None,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a change entry for *vault_path* and return it.

    Parameters
    ----------
    vault_path: path to the .vault file that was changed.
    action:     short label, e.g. ``"lock"``, ``"unlock"``, ``"rotate"``.
    actor:      optional identifier (username, email, …).
    note:       optional free-text annotation.
    """
    if not action or not action.strip():
        raise ValueError("action must be a non-empty string")

    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vault": os.path.abspath(vault_path),
        "action": action.strip(),
    }
    if actor:
        entry["actor"] = actor
    if note:
        entry["note"] = note

    path = _get_history_path(vault_path)
    entries = _load_history(path)
    entries.append(entry)
    # keep the log bounded
    if len(entries) > _MAX_ENTRIES:
        entries = entries[-_MAX_ENTRIES:]
    _save_history(path, entries)
    return entry


def read_history(vault_path: str) -> List[Dict[str, Any]]:
    """Return all history entries for *vault_path* (oldest first)."""
    path = _get_history_path(vault_path)
    return _load_history(path)


def clear_history(vault_path: str) -> int:
    """Delete all history entries for *vault_path*; return count removed."""
    path = _get_history_path(vault_path)
    entries = _load_history(path)
    count = len(entries)
    _save_history(path, [])
    return count


def format_history(entries: List[Dict[str, Any]]) -> str:
    """Return a human-readable string representation of *entries*."""
    if not entries:
        return "(no history)"
    lines = []
    for e in entries:
        parts = [e["timestamp"], e["action"]]
        if "actor" in e:
            parts.append(f"by {e['actor']}")
        if "note" in e:
            parts.append(f"({e['note']})")
        lines.append("  ".join(parts))
    return "\n".join(lines)
