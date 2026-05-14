"""Key whitelisting — restrict which env keys are allowed in a vault."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional


def _get_whitelist_path(base_dir: str) -> str:
    return os.path.join(base_dir, ".envault", "whitelist.json")


def _load_whitelist(base_dir: str) -> Dict[str, List[str]]:
    path = _get_whitelist_path(base_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as fh:
        return json.load(fh)


def _save_whitelist(base_dir: str, data: Dict[str, List[str]]) -> None:
    path = _get_whitelist_path(base_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def set_whitelist(base_dir: str, vault: str, keys: List[str]) -> Dict:
    """Set (replace) the allowed-key whitelist for *vault*."""
    if not keys:
        raise ValueError("keys list must not be empty")
    data = _load_whitelist(base_dir)
    data[vault] = sorted(set(keys))
    _save_whitelist(base_dir, data)
    return {"vault": vault, "allowed_keys": data[vault]}


def get_whitelist(base_dir: str, vault: str) -> Optional[List[str]]:
    """Return the whitelist for *vault*, or None if no whitelist is set."""
    return _load_whitelist(base_dir).get(vault)


def remove_whitelist(base_dir: str, vault: str) -> bool:
    """Remove the whitelist for *vault*. Returns True if one existed."""
    data = _load_whitelist(base_dir)
    if vault not in data:
        return False
    del data[vault]
    _save_whitelist(base_dir, data)
    return True


def check_keys(base_dir: str, vault: str, keys: List[str]) -> Dict:
    """Check *keys* against the whitelist for *vault*.

    Returns a dict with 'allowed', 'denied', and 'whitelisted' lists.
    If no whitelist is configured, all keys are considered allowed.
    """
    whitelist = get_whitelist(base_dir, vault)
    if whitelist is None:
        return {"allowed": list(keys), "denied": [], "whitelisted": None}
    allowed = [k for k in keys if k in whitelist]
    denied = [k for k in keys if k not in whitelist]
    return {"allowed": allowed, "denied": denied, "whitelisted": whitelist}
