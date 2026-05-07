"""Compare two vault files side-by-side, reporting differences in keys and values."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import unlock


@dataclass
class CompareResult:
    left_path: str
    right_path: str
    only_in_left: List[str] = field(default_factory=list)
    only_in_right: List[str] = field(default_factory=list)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (left_val, right_val)
    unchanged: List[str] = field(default_factory=list)

    def has_differences(self) -> bool:
        return bool(self.only_in_left or self.only_in_right or self.changed)


def compare_vaults(
    left_path: str,
    right_path: str,
    key: str,
    left_key: Optional[str] = None,
    right_key: Optional[str] = None,
    mask_values: bool = True,
) -> CompareResult:
    """Decrypt and compare two vault files using the provided key(s)."""
    lk = left_key or key
    rk = right_key or key

    left_env = unlock(Path(left_path).read_text(), lk)
    right_env = unlock(Path(right_path).read_text(), rk)

    all_keys = set(left_env) | set(right_env)
    result = CompareResult(left_path=left_path, right_path=right_path)

    for k in sorted(all_keys):
        in_left = k in left_env
        in_right = k in right_env
        if in_left and not in_right:
            result.only_in_left.append(k)
        elif in_right and not in_left:
            result.only_in_right.append(k)
        elif left_env[k] != right_env[k]:
            if mask_values:
                result.changed[k] = ("***", "***")
            else:
                result.changed[k] = (left_env[k], right_env[k])
        else:
            result.unchanged.append(k)

    return result


def format_compare(result: CompareResult) -> str:
    """Return a human-readable comparison report."""
    lines = [
        f"Comparing: {result.left_path}  <->  {result.right_path}",
        "",
    ]
    if not result.has_differences():
        lines.append("No differences found.")
        return "\n".join(lines)

    for k in result.only_in_left:
        lines.append(f"  < {k}  (only in left)")
    for k in result.only_in_right:
        lines.append(f"  > {k}  (only in right)")
    for k, (lv, rv) in result.changed.items():
        lines.append(f"  ~ {k}  [{lv}] -> [{rv}]")

    lines.append("")
    lines.append(
        f"{len(result.only_in_left)} only-left  "
        f"{len(result.only_in_right)} only-right  "
        f"{len(result.changed)} changed  "
        f"{len(result.unchanged)} unchanged"
    )
    return "\n".join(lines)
