"""Scope management: restrict vault operations to a named environment scope."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

_SCOPES_FILE = "scopes.json"


def _get_scopes_path(base_dir: str) -> Path:
    return Path(base_dir) / _SCOPES_FILE


def _load_scopes(path: Path) -> Dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_scopes(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def add_scope(base_dir: str, name: str, vault_path: str, description: str = "") -> Dict:
    """Register a named scope pointing to a vault file."""
    if not name or not name.strip():
        raise ValueError("Scope name must not be empty")
    if not vault_path or not vault_path.strip():
        raise ValueError("vault_path must not be empty")

    path = _get_scopes_path(base_dir)
    scopes = _load_scopes(path)

    if name in scopes:
        raise KeyError(f"Scope '{name}' already exists")

    entry = {"vault": vault_path, "description": description}
    scopes[name] = entry
    _save_scopes(path, scopes)
    return {"name": name, **entry}


def remove_scope(base_dir: str, name: str) -> None:
    """Remove a registered scope by name."""
    path = _get_scopes_path(base_dir)
    scopes = _load_scopes(path)
    if name not in scopes:
        raise KeyError(f"Scope '{name}' not found")
    del scopes[name]
    _save_scopes(path, scopes)


def get_scope(base_dir: str, name: str) -> Optional[Dict]:
    """Return scope entry or None if not found."""
    scopes = _load_scopes(_get_scopes_path(base_dir))
    entry = scopes.get(name)
    if entry is None:
        return None
    return {"name": name, **entry}


def list_scopes(base_dir: str) -> List[Dict]:
    """Return all registered scopes."""
    scopes = _load_scopes(_get_scopes_path(base_dir))
    return [{"name": k, **v} for k, v in scopes.items()]
