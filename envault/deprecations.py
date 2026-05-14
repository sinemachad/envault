"""Track and report deprecated environment variable keys."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


def _get_deprecations_path(base_dir: str) -> Path:
    return Path(base_dir) / ".envault" / "deprecations.json"


def _load_deprecations(path: Path) -> Dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_deprecations(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


@dataclass
class DeprecationEntry:
    key: str
    reason: str
    replacement: Optional[str] = None
    since: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "reason": self.reason,
            "replacement": self.replacement,
            "since": self.since,
        }


def add_deprecation(
    key: str,
    reason: str,
    base_dir: str = ".",
    replacement: Optional[str] = None,
    since: Optional[str] = None,
) -> DeprecationEntry:
    path = _get_deprecations_path(base_dir)
    data = _load_deprecations(path)
    entry = DeprecationEntry(key=key, reason=reason, replacement=replacement, since=since)
    data[key] = entry.to_dict()
    _save_deprecations(path, data)
    return entry


def remove_deprecation(key: str, base_dir: str = ".") -> bool:
    path = _get_deprecations_path(base_dir)
    data = _load_deprecations(path)
    if key not in data:
        return False
    del data[key]
    _save_deprecations(path, data)
    return True


def list_deprecations(base_dir: str = ".") -> List[DeprecationEntry]:
    path = _get_deprecations_path(base_dir)
    data = _load_deprecations(path)
    return [
        DeprecationEntry(
            key=v["key"],
            reason=v["reason"],
            replacement=v.get("replacement"),
            since=v.get("since"),
        )
        for v in data.values()
    ]


def check_env_deprecations(
    env: Dict[str, str], base_dir: str = "."
) -> List[DeprecationEntry]:
    """Return deprecation entries for any keys present in env."""
    path = _get_deprecations_path(base_dir)
    data = _load_deprecations(path)
    found = []
    for key in env:
        if key in data:
            v = data[key]
            found.append(
                DeprecationEntry(
                    key=v["key"],
                    reason=v["reason"],
                    replacement=v.get("replacement"),
                    since=v.get("since"),
                )
            )
    return found
