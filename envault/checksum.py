"""Checksum utilities for verifying vault file integrity."""

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Optional

_CHECKSUM_VERSION = 1


@dataclass
class ChecksumEntry:
    vault_path: str
    algorithm: str
    digest: str
    version: int = _CHECKSUM_VERSION

    def __repr__(self) -> str:
        return (
            f"ChecksumEntry(vault={self.vault_path!r}, "
            f"alg={self.algorithm!r}, digest={self.digest[:8]!r}...)"
        )


def _get_checksum_path(vault_path: str) -> str:
    base = os.path.splitext(vault_path)[0]
    return base + ".checksum.json"


def compute_checksum(vault_path: str, algorithm: str = "sha256") -> ChecksumEntry:
    """Compute a checksum for the given vault file."""
    if algorithm not in hashlib.algorithms_guaranteed:
        raise ValueError(f"Unsupported algorithm: {algorithm!r}")
    if not os.path.exists(vault_path):
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    h = hashlib.new(algorithm)
    with open(vault_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)

    return ChecksumEntry(
        vault_path=os.path.abspath(vault_path),
        algorithm=algorithm,
        digest=h.hexdigest(),
    )


def save_checksum(entry: ChecksumEntry) -> str:
    """Persist a ChecksumEntry to disk. Returns the checksum file path."""
    path = _get_checksum_path(entry.vault_path)
    data = {
        "version": entry.version,
        "vault_path": entry.vault_path,
        "algorithm": entry.algorithm,
        "digest": entry.digest,
    }
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
    return path


def load_checksum(vault_path: str) -> Optional[ChecksumEntry]:
    """Load a persisted ChecksumEntry for the given vault. Returns None if absent."""
    path = _get_checksum_path(os.path.abspath(vault_path))
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        data = json.load(fh)
    return ChecksumEntry(
        vault_path=data["vault_path"],
        algorithm=data["algorithm"],
        digest=data["digest"],
        version=data.get("version", _CHECKSUM_VERSION),
    )


def verify_checksum(vault_path: str) -> bool:
    """Return True if the vault file matches its stored checksum, False otherwise."""
    stored = load_checksum(vault_path)
    if stored is None:
        raise FileNotFoundError(f"No checksum found for: {vault_path}")
    current = compute_checksum(vault_path, algorithm=stored.algorithm)
    return current.digest == stored.digest
