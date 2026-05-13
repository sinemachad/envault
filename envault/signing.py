"""Vault signing — attach and verify HMAC signatures on encrypted vault files."""

import hashlib
import hmac
import json
import os
import time
from typing import Optional


SIGNATURE_VERSION = 1


class SignatureError(Exception):
    """Raised when signature verification fails."""


class SignatureEntry:
    def __init__(self, digest: str, algorithm: str, signed_at: float, version: int):
        self.digest = digest
        self.algorithm = algorithm
        self.signed_at = signed_at
        self.version = version

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SignatureEntry(algorithm={self.algorithm!r}, "
            f"signed_at={self.signed_at}, digest={self.digest[:12]!r}...)"
        )

    def to_dict(self) -> dict:
        return {
            "digest": self.digest,
            "algorithm": self.algorithm,
            "signed_at": self.signed_at,
            "version": self.version,
        }


def _get_sig_path(vault_path: str) -> str:
    """Return the .sig sidecar path for a given vault file."""
    return vault_path + ".sig"


def sign_vault(vault_path: str, key: str, algorithm: str = "sha256") -> SignatureEntry:
    """Compute an HMAC signature over the vault file contents and write a sidecar."""
    if not os.path.isfile(vault_path):
        raise FileNotFoundError(f"Vault file not found: {vault_path}")
    if not key:
        raise ValueError("Key must not be empty")

    with open(vault_path, "rb") as fh:
        data = fh.read()

    mac = hmac.new(key.encode(), data, getattr(hashlib, algorithm))
    entry = SignatureEntry(
        digest=mac.hexdigest(),
        algorithm=algorithm,
        signed_at=time.time(),
        version=SIGNATURE_VERSION,
    )
    sig_path = _get_sig_path(vault_path)
    with open(sig_path, "w") as fh:
        json.dump(entry.to_dict(), fh, indent=2)
    return entry


def verify_vault(vault_path: str, key: str) -> SignatureEntry:
    """Verify a vault file against its sidecar signature. Raises SignatureError on mismatch."""
    sig_path = _get_sig_path(vault_path)
    if not os.path.isfile(sig_path):
        raise SignatureError(f"No signature file found for: {vault_path}")
    if not os.path.isfile(vault_path):
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    with open(sig_path) as fh:
        meta = json.load(fh)

    algorithm = meta.get("algorithm", "sha256")
    expected = meta["digest"]

    with open(vault_path, "rb") as fh:
        data = fh.read()

    mac = hmac.new(key.encode(), data, getattr(hashlib, algorithm))
    actual = mac.hexdigest()

    if not hmac.compare_digest(expected, actual):
        raise SignatureError("Vault signature mismatch — file may have been tampered with.")

    return SignatureEntry(
        digest=meta["digest"],
        algorithm=algorithm,
        signed_at=meta["signed_at"],
        version=meta.get("version", SIGNATURE_VERSION),
    )


def remove_signature(vault_path: str) -> bool:
    """Remove the sidecar signature file if it exists. Returns True if removed."""
    sig_path = _get_sig_path(vault_path)
    if os.path.isfile(sig_path):
        os.remove(sig_path)
        return True
    return False
