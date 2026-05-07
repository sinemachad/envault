"""Merge two .env vault files, with conflict resolution strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from envault.vault import lock, unlock

Strategy = Literal["ours", "theirs", "union"]


@dataclass
class MergeConflict:
    key: str
    ours: str
    theirs: str


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[MergeConflict] = field(default_factory=list)
    added_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)


def has_conflicts(result: MergeResult) -> bool:
    return len(result.conflicts) > 0


def merge_envs(
    base: Dict[str, str],
    ours: Dict[str, str],
    theirs: Dict[str, str],
    strategy: Strategy = "ours",
) -> MergeResult:
    """Three-way merge of env dicts using *base* as the common ancestor."""
    all_keys = set(base) | set(ours) | set(theirs)
    merged: Dict[str, str] = {}
    conflicts: List[MergeConflict] = []
    added_keys: List[str] = []
    removed_keys: List[str] = []

    for key in sorted(all_keys):
        in_base = key in base
        in_ours = key in ours
        in_theirs = key in theirs

        if not in_ours and not in_theirs:
            # Deleted by both sides — omit
            removed_keys.append(key)
            continue

        if not in_base and (in_ours or in_theirs):
            added_keys.append(key)

        val_base = base.get(key)
        val_ours = ours.get(key)
        val_theirs = theirs.get(key)

        ours_changed = in_ours and val_ours != val_base
        theirs_changed = in_theirs and val_theirs != val_base

        if not in_ours:
            # Deleted by ours, kept by theirs
            if strategy == "theirs" or strategy == "union":
                merged[key] = val_theirs  # type: ignore[assignment]
            # else "ours" — omit
            continue

        if not in_theirs:
            # Deleted by theirs, kept by ours
            merged[key] = val_ours  # type: ignore[assignment]
            continue

        if not ours_changed:
            merged[key] = val_theirs  # type: ignore[assignment]
        elif not theirs_changed:
            merged[key] = val_ours  # type: ignore[assignment]
        elif val_ours == val_theirs:
            merged[key] = val_ours  # type: ignore[assignment]
        else:
            # True conflict
            conflicts.append(MergeConflict(key=key, ours=val_ours, theirs=val_theirs))  # type: ignore[arg-type]
            if strategy == "ours":
                merged[key] = val_ours  # type: ignore[assignment]
            else:
                merged[key] = val_theirs  # type: ignore[assignment]

    return MergeResult(
        merged=merged,
        conflicts=conflicts,
        added_keys=added_keys,
        removed_keys=removed_keys,
    )


def merge_vaults(
    base_path: str,
    ours_path: str,
    theirs_path: str,
    key: str,
    output_path: str,
    strategy: Strategy = "ours",
) -> MergeResult:
    """Decrypt three vault files, merge them, and write the result."""
    base = unlock(base_path, key)
    ours = unlock(ours_path, key)
    theirs = unlock(theirs_path, key)

    result = merge_envs(base, ours, theirs, strategy=strategy)
    lock(result.merged, output_path, key)
    return result
