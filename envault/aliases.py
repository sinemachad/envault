"""Key aliasing — map short names to full env variable names."""

import json
import os
from typing import Dict, List, Optional

_ALIASES_FILE = "aliases.json"


def _get_aliases_path(base_dir: str) -> str:
    return os.path.join(base_dir, _ALIASES_FILE)


def _load_aliases(base_dir: str) -> Dict[str, str]:
    path = _get_aliases_path(base_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_aliases(base_dir: str, data: Dict[str, str]) -> None:
    os.makedirs(base_dir, exist_ok=True)
    with open(_get_aliases_path(base_dir), "w") as f:
        json.dump(data, f, indent=2)


def add_alias(alias: str, target: str, base_dir: str = ".") -> Dict[str, str]:
    """Register *alias* as a short name for *target* key."""
    if not alias or not target:
        raise ValueError("alias and target must be non-empty strings")
    data = _load_aliases(base_dir)
    data[alias] = target
    _save_aliases(base_dir, data)
    return {"alias": alias, "target": target}


def remove_alias(alias: str, base_dir: str = ".") -> None:
    """Remove *alias* from the alias registry."""
    data = _load_aliases(base_dir)
    if alias not in data:
        raise KeyError(f"alias '{alias}' not found")
    del data[alias]
    _save_aliases(base_dir, data)


def resolve_alias(alias: str, base_dir: str = ".") -> Optional[str]:
    """Return the target key for *alias*, or None if not registered."""
    return _load_aliases(base_dir).get(alias)


def list_aliases(base_dir: str = ".") -> List[Dict[str, str]]:
    """Return all aliases as a list of {alias, target} dicts."""
    data = _load_aliases(base_dir)
    return [{"alias": k, "target": v} for k, v in sorted(data.items())]
