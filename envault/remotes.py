"""Remote backend support for syncing encrypted vaults."""

import json
import os
from pathlib import Path
from typing import Optional

_REMOTES_FILE = "remotes.json"


def _get_remotes_path(base_dir: Optional[str] = None) -> Path:
    root = Path(base_dir) if base_dir else Path.home() / ".envault"
    root.mkdir(parents=True, exist_ok=True)
    return root / _REMOTES_FILE


def _load_remotes(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_remotes(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))


def add_remote(name: str, url: str, base_dir: Optional[str] = None) -> dict:
    """Register a named remote URL for vault sync."""
    if not name or not name.isidentifier():
        raise ValueError(f"Invalid remote name: {name!r}")
    if not url.startswith(("http://", "https://", "s3://", "file://")):
        raise ValueError(f"Unsupported URL scheme: {url!r}")
    path = _get_remotes_path(base_dir)
    remotes = _load_remotes(path)
    entry = {"name": name, "url": url}
    remotes[name] = entry
    _save_remotes(path, remotes)
    return entry


def remove_remote(name: str, base_dir: Optional[str] = None) -> None:
    """Remove a registered remote by name."""
    path = _get_remotes_path(base_dir)
    remotes = _load_remotes(path)
    if name not in remotes:
        raise KeyError(f"Remote not found: {name!r}")
    del remotes[name]
    _save_remotes(path, remotes)


def get_remote(name: str, base_dir: Optional[str] = None) -> dict:
    """Return the entry for a single named remote."""
    path = _get_remotes_path(base_dir)
    remotes = _load_remotes(path)
    if name not in remotes:
        raise KeyError(f"Remote not found: {name!r}")
    return remotes[name]


def list_remotes(base_dir: Optional[str] = None) -> list:
    """Return all registered remotes as a list of dicts."""
    path = _get_remotes_path(base_dir)
    return list(_load_remotes(path).values())
