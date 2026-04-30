"""Tag management for envault vault files."""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

_TAGS_FILENAME = ".envault_tags.json"


def _get_tags_path(base_dir: Optional[str] = None) -> Path:
    base = Path(base_dir) if base_dir else Path.cwd()
    return base / _TAGS_FILENAME


def _load_tags(base_dir: Optional[str] = None) -> Dict[str, List[str]]:
    path = _get_tags_path(base_dir)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_tags(data: Dict[str, List[str]], base_dir: Optional[str] = None) -> None:
    path = _get_tags_path(base_dir)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def add_tag(vault_file: str, tag: str, base_dir: Optional[str] = None) -> Dict[str, List[str]]:
    """Associate a tag with a vault file."""
    data = _load_tags(base_dir)
    tags = data.get(vault_file, [])
    if tag not in tags:
        tags.append(tag)
    data[vault_file] = tags
    _save_tags(data, base_dir)
    return {"vault_file": vault_file, "tags": tags}


def remove_tag(vault_file: str, tag: str, base_dir: Optional[str] = None) -> Dict[str, List[str]]:
    """Remove a tag from a vault file."""
    data = _load_tags(base_dir)
    tags = data.get(vault_file, [])
    if tag not in tags:
        raise ValueError(f"Tag '{tag}' not found on '{vault_file}'")
    tags.remove(tag)
    data[vault_file] = tags
    _save_tags(data, base_dir)
    return {"vault_file": vault_file, "tags": tags}


def list_tags(vault_file: str, base_dir: Optional[str] = None) -> List[str]:
    """Return all tags for a vault file."""
    data = _load_tags(base_dir)
    return data.get(vault_file, [])


def find_by_tag(tag: str, base_dir: Optional[str] = None) -> List[str]:
    """Return all vault files that have the given tag."""
    data = _load_tags(base_dir)
    return [vf for vf, tags in data.items() if tag in tags]
