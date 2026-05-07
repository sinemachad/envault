"""Export decrypted .env variables to various output formats."""

import json
from typing import Dict, List, Optional

FORMAT_DOTENV = "dotenv"
FORMAT_JSON = "json"
FORMAT_SHELL = "shell"
FORMAT_CSV = "csv"

SUPPORTED_FORMATS = [FORMAT_DOTENV, FORMAT_JSON, FORMAT_SHELL, FORMAT_CSV]


class ExportResult:
    def __init__(self, fmt: str, content: str, keys: List[str]):
        self.format = fmt
        self.content = content
        self.keys = keys
        self.count = len(keys)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ExportResult(format={self.format!r}, count={self.count})"


def _filter_keys(env: Dict[str, str], keys: Optional[List[str]]) -> Dict[str, str]:
    if not keys:
        return dict(env)
    return {k: v for k, v in env.items() if k in keys}


def export_env(env: Dict[str, str], fmt: str, keys: Optional[List[str]] = None) -> ExportResult:
    """Serialize *env* dict to the requested *fmt* string.

    Args:
        env:  Decrypted key/value pairs.
        fmt:  One of the SUPPORTED_FORMATS constants.
        keys: Optional allow-list of keys to include.

    Returns:
        ExportResult with rendered content.

    Raises:
        ValueError: If *fmt* is not supported.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format {fmt!r}. Choose from: {SUPPORTED_FORMATS}")

    subset = _filter_keys(env, keys)

    if fmt == FORMAT_DOTENV:
        lines = [f"{k}={v}" for k, v in subset.items()]
        content = "\n".join(lines)
    elif fmt == FORMAT_JSON:
        content = json.dumps(subset, indent=2)
    elif fmt == FORMAT_SHELL:
        lines = [f"export {k}={v}" for k, v in subset.items()]
        content = "\n".join(lines)
    elif fmt == FORMAT_CSV:
        rows = ["key,value"] + [f"{k},{v}" for k, v in subset.items()]
        content = "\n".join(rows)
    else:  # pragma: no cover
        content = ""

    return ExportResult(fmt=fmt, content=content, keys=list(subset.keys()))
