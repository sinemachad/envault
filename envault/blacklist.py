"""Blacklist module: prevents specific keys from being stored in a vault."""

import json
import os
from pathlib import Path


def _get_blacklist_path(base_dir: str) -> Path:
    return Path(base_dir) / ".envault" / "blacklist.json"


def _load_blacklist(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_blacklist(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def set_blacklist(base_dir: str, vault: str, keys: list) -> dict:
    """Set the blacklisted keys for a vault, replacing any existing list."""
    if not keys:
        raise ValueError("keys list must not be empty")
    path = _get_blacklist_path(base_dir)
    data = _load_blacklist(path)
    entry = {
        "vault": vault,
        "keys": sorted(set(keys)),
    }
    data[vault] = entry
    _save_blacklist(path, data)
    return entry


def get_blacklist(base_dir: str, vault: str) -> list:
    """Return the blacklisted keys for a vault, or an empty list."""
    path = _get_blacklist_path(base_dir)
    data = _load_blacklist(path)
    return data.get(vault, {}).get("keys", [])


def remove_blacklist(base_dir: str, vault: str) -> bool:
    """Remove the blacklist entry for a vault. Returns True if removed."""
    path = _get_blacklist_path(base_dir)
    data = _load_blacklist(path)
    if vault not in data:
        return False
    del data[vault]
    _save_blacklist(path, data)
    return True


def check_blacklist(base_dir: str, vault: str, keys: list) -> list:
    """Return any keys that are blacklisted for the given vault."""
    blacklisted = set(get_blacklist(base_dir, vault))
    return [k for k in keys if k in blacklisted]
