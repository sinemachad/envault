"""Diff utilities for comparing .env file versions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class EnvDiff:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    unchanged: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_envs(
    old: Dict[str, str],
    new: Dict[str, str],
    mask_values: bool = True,
) -> EnvDiff:
    """Compare two env dicts and return a structured diff."""
    result = EnvDiff()
    old_keys = set(old)
    new_keys = set(new)

    for key in new_keys - old_keys:
        result.added[key] = _maybe_mask(new[key], mask_values)

    for key in old_keys - new_keys:
        result.removed[key] = _maybe_mask(old[key], mask_values)

    for key in old_keys & new_keys:
        if old[key] != new[key]:
            result.changed[key] = (
                _maybe_mask(old[key], mask_values),
                _maybe_mask(new[key], mask_values),
            )
        else:
            result.unchanged[key] = _maybe_mask(old[key], mask_values)

    return result


def format_diff(diff: EnvDiff) -> str:
    """Return a human-readable string representation of an EnvDiff."""
    lines: List[str] = []

    for key, val in sorted(diff.added.items()):
        lines.append(f"+ {key}={val}")

    for key, val in sorted(diff.removed.items()):
        lines.append(f"- {key}={val}")

    for key, (old_val, new_val) in sorted(diff.changed.items()):
        lines.append(f"~ {key}: {old_val} -> {new_val}")

    if not lines:
        lines.append("No changes.")

    return "\n".join(lines)


def _maybe_mask(value: str, mask: bool) -> str:
    if mask and value:
        visible = value[:2] if len(value) > 4 else ""
        return visible + "***"
    return value
