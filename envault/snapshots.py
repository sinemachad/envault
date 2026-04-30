"""Snapshot management: save and restore named snapshots of vault files."""

import json
import os
import time
from pathlib import Path
from typing import Optional

from envault.vault import lock, unlock


def _get_snapshots_dir(base_dir: Optional[str] = None) -> Path:
    base = Path(base_dir) if base_dir else Path.home() / ".envault"
    snapshots_dir = base / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    return snapshots_dir


def _index_path(snapshots_dir: Path) -> Path:
    return snapshots_dir / "index.json"


def _load_index(snapshots_dir: Path) -> dict:
    path = _index_path(snapshots_dir)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_index(snapshots_dir: Path, index: dict) -> None:
    with open(_index_path(snapshots_dir), "w") as f:
        json.dump(index, f, indent=2)


def save_snapshot(name: str, vault_path: str, key: str, base_dir: Optional[str] = None) -> dict:
    """Save a named snapshot of the current vault file."""
    snapshots_dir = _get_snapshots_dir(base_dir)
    index = _load_index(snapshots_dir)

    if not os.path.exists(vault_path):
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    with open(vault_path, "r") as f:
        encrypted_content = f.read()

    # Verify the key can decrypt the vault before snapshotting
    unlock(vault_path, key)  # raises on failure

    snapshot_file = snapshots_dir / f"{name}.vault"
    with open(snapshot_file, "w") as f:
        f.write(encrypted_content)

    entry = {
        "name": name,
        "vault_path": str(vault_path),
        "snapshot_file": str(snapshot_file),
        "created_at": time.time(),
    }
    index[name] = entry
    _save_index(snapshots_dir, index)
    return entry


def restore_snapshot(name: str, vault_path: str, key: str, base_dir: Optional[str] = None) -> None:
    """Restore a named snapshot to the vault file path."""
    snapshots_dir = _get_snapshots_dir(base_dir)
    index = _load_index(snapshots_dir)

    if name not in index:
        raise KeyError(f"Snapshot '{name}' not found")

    snapshot_file = Path(index[name]["snapshot_file"])
    if not snapshot_file.exists():
        raise FileNotFoundError(f"Snapshot data missing: {snapshot_file}")

    with open(snapshot_file, "r") as f:
        content = f.read()

    with open(vault_path, "w") as f:
        f.write(content)


def list_snapshots(base_dir: Optional[str] = None) -> list:
    """Return list of snapshot metadata dicts, sorted by creation time."""
    snapshots_dir = _get_snapshots_dir(base_dir)
    index = _load_index(snapshots_dir)
    return sorted(index.values(), key=lambda e: e["created_at"])


def delete_snapshot(name: str, base_dir: Optional[str] = None) -> None:
    """Delete a named snapshot."""
    snapshots_dir = _get_snapshots_dir(base_dir)
    index = _load_index(snapshots_dir)

    if name not in index:
        raise KeyError(f"Snapshot '{name}' not found")

    snapshot_file = Path(index[name]["snapshot_file"])
    if snapshot_file.exists():
        snapshot_file.unlink()

    del index[name]
    _save_index(snapshots_dir, index)
