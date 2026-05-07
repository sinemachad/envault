"""Redaction utilities for masking sensitive values in .env output."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

_DEFAULT_PATTERNS = [
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "private_key", "auth", "credential", "access_key", "signing_key",
]

MASK = "****"


@dataclass
class RedactResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RedactResult(total={len(self.original)}, "
            f"masked={len(self.masked_keys)})"
        )


def _key_is_sensitive(key: str, patterns: List[str]) -> bool:
    """Return True if the key name matches any sensitive pattern."""
    lower = key.lower()
    return any(pat in lower for pat in patterns)


def redact_env(
    env: Dict[str, str],
    extra_patterns: Optional[List[str]] = None,
    custom_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Mask sensitive values in an env dict.

    Args:
        env: Mapping of key -> value.
        extra_patterns: Additional substrings that mark a key as sensitive.
        custom_keys: Explicit list of keys to always mask regardless of name.

    Returns:
        A RedactResult with the masked copy and the list of masked keys.
    """
    patterns = list(_DEFAULT_PATTERNS)
    if extra_patterns:
        patterns.extend(p.lower() for p in extra_patterns)

    force_keys = set(custom_keys or [])

    redacted: Dict[str, str] = {}
    masked_keys: List[str] = []

    for key, value in env.items():
        if key in force_keys or _key_is_sensitive(key, patterns):
            redacted[key] = MASK
            masked_keys.append(key)
        else:
            redacted[key] = value

    return RedactResult(original=env, redacted=redacted, masked_keys=masked_keys)


def format_redacted(result: RedactResult) -> str:
    """Render a redacted env dict as .env-style text."""
    lines = [f"{k}={v}" for k, v in result.redacted.items()]
    return "\n".join(lines)
