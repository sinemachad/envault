"""Profile management for envault — allows multiple named vaults per project."""

import os
import json
from pathlib import Path

DEFAULT_PROFILE = "default"
PROFILES_DIR = ".envault"
PROFILE_INDEX = "profiles.json"


def _get_profiles_path(base_dir: str = ".") -> Path:
    return Path(base_dir) / PROFILES_DIR / PROFILE_INDEX


def _load_index(base_dir: str = ".") -> dict:
    path = _get_profiles_path(base_dir)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_index(index: dict, base_dir: str = ".") -> None:
    path = _get_profiles_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(index, f, indent=2)


def add_profile(name: str, vault_file: str, base_dir: str = ".") -> dict:
    """Register a named profile pointing to a vault file."""
    index = _load_index(base_dir)
    if name in index:
        raise ValueError(f"Profile '{name}' already exists.")
    index[name] = {"vault_file": vault_file}
    _save_index(index, base_dir)
    return index[name]


def remove_profile(name: str, base_dir: str = ".") -> None:
    """Remove a named profile from the index."""
    index = _load_index(base_dir)
    if name not in index:
        raise KeyError(f"Profile '{name}' not found.")
    del index[name]
    _save_index(index, base_dir)


def get_profile(name: str, base_dir: str = ".") -> dict:
    """Retrieve profile metadata by name."""
    index = _load_index(base_dir)
    if name not in index:
        raise KeyError(f"Profile '{name}' not found.")
    return index[name]


def list_profiles(base_dir: str = ".") -> list:
    """Return a list of all registered profile names."""
    return list(_load_index(base_dir).keys())
