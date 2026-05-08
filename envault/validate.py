"""Validation module: check a decrypted .env against expected types and constraints."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ValidationError:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message}"


@dataclass
class ValidationResult:
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:  # pragma: no cover
        status = "valid" if self.valid else f"{len(self.errors)} error(s)"
        return f"<ValidationResult {status}>"


# ---------------------------------------------------------------------------
# Built-in type checkers
# ---------------------------------------------------------------------------

_TYPE_CHECKERS: Dict[str, Any] = {
    "str": lambda v: isinstance(v, str),
    "int": lambda v: v.lstrip("-").isdigit(),
    "bool": lambda v: v.lower() in ("true", "false", "1", "0", "yes", "no"),
    "url": lambda v: re.match(r"^https?://", v) is not None,
    "email": lambda v: re.match(r"^[^@]+@[^@]+\.[^@]+$", v) is not None,
}


def _check_type(value: str, type_name: str) -> bool:
    checker = _TYPE_CHECKERS.get(type_name)
    if checker is None:
        raise ValueError(f"Unknown type '{type_name}'")
    return checker(value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_env(
    env: Dict[str, str],
    rules: List[Dict[str, Any]],
) -> ValidationResult:
    """Validate *env* against a list of rule dicts.

    Each rule may contain:
      - ``key``      (str, required): the env variable name.
      - ``required`` (bool, default False): error if key is absent or empty.
      - ``type``     (str, optional): one of str/int/bool/url/email.
      - ``pattern``  (str, optional): regex the value must fully match.
    """
    result = ValidationResult()

    for rule in rules:
        key: str = rule["key"]
        value: Optional[str] = env.get(key)
        required: bool = rule.get("required", False)

        if value is None or value == "":
            if required:
                result.errors.append(ValidationError(key, "required but missing or empty"))
            continue

        type_name: Optional[str] = rule.get("type")
        if type_name:
            try:
                if not _check_type(value, type_name):
                    result.errors.append(ValidationError(key, f"expected type '{type_name}'"))
            except ValueError as exc:
                result.errors.append(ValidationError(key, str(exc)))

        pattern: Optional[str] = rule.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            result.errors.append(ValidationError(key, f"does not match pattern '{pattern}'"))

    return result


def format_validation(result: ValidationResult) -> str:
    """Return a human-readable summary of *result*."""
    if result.valid:
        return "All checks passed."
    lines = [f"  - {e}" for e in result.errors]
    return "Validation failed:\n" + "\n".join(lines)
