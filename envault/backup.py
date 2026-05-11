"""Backup and restore encrypted vault files to/from a local archive directory."""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _get_backups_dir(base_dir: str) -> Path:
    path = Path(base_dir) / ".envault" / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path(base_dir: str) -> Path:
    return _get_backups_dir(base_dir) / "index.json"


def _load_index(base_dir: str) -> List[Dict]:
    path = _index_path(base_dir)
    if not path.exists():
        return []
    with open(path, "r") as fh:
        return json.load(fh)


def _save_index(base_dir: str, index: List[Dict]) -> None:
    with open(_index_path(base_dir), "w") as fh:
        json.dump(index, fh, indent=2)


def create_backup(vault_path: str, base_dir: str, label: Optional[str] = None) -> Dict:
    """Copy the vault file into the backup archive and record metadata."""
    if not os.path.exists(vault_path):
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    backups_dir = _get_backups_dir(base_dir)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_ts = timestamp.replace(":", "-").replace("+", "Z")
    backup_filename = f"backup_{safe_ts}.env.vault"
    dest = backups_dir / backup_filename
    shutil.copy2(vault_path, dest)

    entry = {
        "id": backup_filename,
        "timestamp": timestamp,
        "label": label or "",
        "source": str(vault_path),
        "file": str(dest),
    }
    index = _load_index(base_dir)
    index.append(entry)
    _save_index(base_dir, index)
    return entry


def list_backups(base_dir: str) -> List[Dict]:
    """Return all backup entries sorted newest-first."""
    return list(reversed(_load_index(base_dir)))


def restore_backup(backup_id: str, dest_path: str, base_dir: str) -> Dict:
    """Restore a backup file to *dest_path* by its ID."""
    index = _load_index(base_dir)
    entry = next((e for e in index if e["id"] == backup_id), None)
    if entry is None:
        raise KeyError(f"Backup not found: {backup_id}")
    shutil.copy2(entry["file"], dest_path)
    return entry


def delete_backup(backup_id: str, base_dir: str) -> Dict:
    """Remove a backup file and its index entry."""
    index = _load_index(base_dir)
    entry = next((e for e in index if e["id"] == backup_id), None)
    if entry is None:
        raise KeyError(f"Backup not found: {backup_id}")
    try:
        os.remove(entry["file"])
    except FileNotFoundError:
        pass
    new_index = [e for e in index if e["id"] != backup_id]
    _save_index(base_dir, new_index)
    return entry
