"""Sharing module: export/import encrypted vault bundles for team sharing."""

import json
import base64
from pathlib import Path
from typing import Optional

from envault.crypto import derive_key, encrypt, decrypt
from envault.vault import parse_env, serialize_env, lock, unlock


BUNDLE_VERSION = 1


def export_bundle(env_path: str, passphrase: str, output_path: Optional[str] = None) -> str:
    """Encrypt an .env file and export it as a shareable JSON bundle.

    Args:
        env_path: Path to the plaintext .env file.
        passphrase: Shared passphrase used to derive the encryption key.
        output_path: Optional path to write the bundle JSON file.

    Returns:
        The bundle as a JSON string.
    """
    env_text = Path(env_path).read_text(encoding="utf-8")
    env_vars = parse_env(env_text)
    serialized = serialize_env(env_vars)

    key = derive_key(passphrase)
    ciphertext = encrypt(serialized, key)

    bundle = {
        "version": BUNDLE_VERSION,
        "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
    }
    bundle_json = json.dumps(bundle, indent=2)

    if output_path:
        Path(output_path).write_text(bundle_json, encoding="utf-8")

    return bundle_json


def import_bundle(bundle_path: str, passphrase: str, output_path: Optional[str] = None) -> dict:
    """Decrypt a bundle file and restore the .env variables.

    Args:
        bundle_path: Path to the encrypted bundle JSON file.
        passphrase: Shared passphrase used to derive the decryption key.
        output_path: Optional path to write the decrypted .env file.

    Returns:
        Dictionary of environment variable key-value pairs.
    """
    bundle_json = Path(bundle_path).read_text(encoding="utf-8")
    bundle = json.loads(bundle_json)

    if bundle.get("version") != BUNDLE_VERSION:
        raise ValueError(f"Unsupported bundle version: {bundle.get('version')}")

    ciphertext = base64.b64decode(bundle["ciphertext"])
    key = derive_key(passphrase)
    plaintext = decrypt(ciphertext, key)

    env_vars = parse_env(plaintext)

    if output_path:
        Path(output_path).write_text(serialize_env(env_vars), encoding="utf-8")

    return env_vars
