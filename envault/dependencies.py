"""Track inter-key dependencies within a vault."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


def _get_deps_path(base_dir: str, vault_path: str) -> str:
    vault_name = Path(vault_path).stem
    return os.path.join(base_dir, f"{vault_name}.deps.json")


def _load_deps(deps_path: str) -> Dict[str, List[str]]:
    if not os.path.exists(deps_path):
        return {}
    with open(deps_path, "r") as fh:
        return json.load(fh)


def _save_deps(deps_path: str, data: Dict[str, List[str]]) -> None:
    os.makedirs(os.path.dirname(deps_path), exist_ok=True)
    with open(deps_path, "w") as fh:
        json.dump(data, fh, indent=2)


def add_dependency(vault_path: str, key: str, depends_on: str, base_dir: str) -> Dict:
    """Record that *key* depends on *depends_on* within the same vault."""
    if key == depends_on:
        raise ValueError("A key cannot depend on itself.")
    deps_path = _get_deps_path(base_dir, vault_path)
    data = _load_deps(deps_path)
    deps = data.get(key, [])
    if depends_on not in deps:
        deps.append(depends_on)
    data[key] = sorted(deps)
    _save_deps(deps_path, data)
    return {"key": key, "depends_on": data[key]}


def remove_dependency(vault_path: str, key: str, depends_on: str, base_dir: str) -> Dict:
    """Remove a recorded dependency."""
    deps_path = _get_deps_path(base_dir, vault_path)
    data = _load_deps(deps_path)
    deps = data.get(key, [])
    if depends_on not in deps:
        raise KeyError(f"No dependency '{depends_on}' found for key '{key}'.")
    deps.remove(depends_on)
    if deps:
        data[key] = deps
    else:
        data.pop(key, None)
    _save_deps(deps_path, data)
    return {"key": key, "depends_on": data.get(key, [])}


def get_dependencies(vault_path: str, key: str, base_dir: str) -> List[str]:
    """Return the list of keys that *key* depends on."""
    deps_path = _get_deps_path(base_dir, vault_path)
    data = _load_deps(deps_path)
    return data.get(key, [])


def list_all_dependencies(vault_path: str, base_dir: str) -> Dict[str, List[str]]:
    """Return the full dependency map for a vault."""
    deps_path = _get_deps_path(base_dir, vault_path)
    return _load_deps(deps_path)


def check_missing(vault_path: str, env: Dict[str, str], base_dir: str) -> Dict[str, List[str]]:
    """Return a mapping of keys whose declared dependencies are absent from *env*."""
    data = list_all_dependencies(vault_path, base_dir)
    missing: Dict[str, List[str]] = {}
    for key, deps in data.items():
        absent = [d for d in deps if d not in env]
        if absent:
            missing[key] = absent
    return missing
