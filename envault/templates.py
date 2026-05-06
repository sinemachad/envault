"""Template support for envault — generate .env files from a template schema."""

from __future__ import annotations

import json
import os
from typing import Any


TEMPLATE_VERSION = 1


def _validate_entry(entry: Any, index: int) -> None:
    if not isinstance(entry, dict):
        raise ValueError(f"Template entry {index} must be a dict")
    if "key" not in entry:
        raise ValueError(f"Template entry {index} missing required field 'key'")
    if not isinstance(entry["key"], str) or not entry["key"].strip():
        raise ValueError(f"Template entry {index} has invalid 'key'")


def load_template(path: str) -> dict:
    """Load and validate a template JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Template root must be a JSON object")
    if "keys" not in data or not isinstance(data["keys"], list):
        raise ValueError("Template must contain a 'keys' list")
    for i, entry in enumerate(data["keys"]):
        _validate_entry(entry, i)
    return data


def generate_env_from_template(template: dict, overrides: dict[str, str] | None = None) -> str:
    """Generate a .env file string from a template dict.

    Each entry may have:
      - key (required): the env var name
      - default (optional): default value
      - description (optional): written as a comment
      - required (optional, bool): if True and no default/override, leaves blank
    """
    overrides = overrides or {}
    lines: list[str] = []
    for entry in template["keys"]:
        key = entry["key"]
        description = entry.get("description", "").strip()
        default = entry.get("default", "")
        value = overrides.get(key, default)
        if description:
            lines.append(f"# {description}")
        lines.append(f"{key}={value}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def check_env_against_template(template: dict, env: dict[str, str]) -> dict:
    """Check an env dict against a template.

    Returns a report dict with:
      - missing: list of required keys absent from env
      - extra: list of keys in env not present in template
    """
    template_keys = {entry["key"] for entry in template["keys"]}
    required_keys = {
        entry["key"]
        for entry in template["keys"]
        if entry.get("required", False)
    }
    env_keys = set(env.keys())
    missing = sorted(required_keys - env_keys)
    extra = sorted(env_keys - template_keys)
    return {"missing": missing, "extra": extra}
