"""Tests for envault.signing."""

import json
import os
import pytest

from envault.crypto import generate_key
from envault.signing import (
    SignatureEntry,
    SignatureError,
    _get_sig_path,
    remove_signature,
    sign_vault,
    verify_vault,
)


@pytest.fixture
def vault_file(tmp_path):
    path = tmp_path / "test.env.vault"
    path.write_text("encrypted-content-placeholder")
    return str(path)


@pytest.fixture
def key():
    return generate_key()


# ---------------------------------------------------------------------------
# sign_vault
# ---------------------------------------------------------------------------

class TestSignVault:
    def test_returns_signature_entry(self, vault_file, key):
        entry = sign_vault(vault_file, key)
        assert isinstance(entry, SignatureEntry)

    def test_digest_is_hex_string(self, vault_file, key):
        entry = sign_vault(vault_file, key)
        int(entry.digest, 16)  # raises ValueError if not hex

    def test_default_algorithm_is_sha256(self, vault_file, key):
        entry = sign_vault(vault_file, key)
        assert entry.algorithm == "sha256"

    def test_sidecar_file_created(self, vault_file, key):
        sign_vault(vault_file, key)
        assert os.path.isfile(_get_sig_path(vault_file))

    def test_sidecar_is_valid_json(self, vault_file, key):
        sign_vault(vault_file, key)
        with open(_get_sig_path(vault_file)) as fh:
            data = json.load(fh)
        assert "digest" in data and "algorithm" in data

    def test_raises_on_missing_vault(self, tmp_path, key):
        with pytest.raises(FileNotFoundError):
            sign_vault(str(tmp_path / "missing.vault"), key)

    def test_raises_on_empty_key(self, vault_file):
        with pytest.raises(ValueError):
            sign_vault(vault_file, "")

    def test_sha512_algorithm_accepted(self, vault_file, key):
        entry = sign_vault(vault_file, key, algorithm="sha512")
        assert entry.algorithm == "sha512"
        assert len(entry.digest) == 128  # sha512 hex digest length


# ---------------------------------------------------------------------------
# verify_vault
# ---------------------------------------------------------------------------

class TestVerifyVault:
    def test_verify_returns_entry_on_success(self, vault_file, key):
        sign_vault(vault_file, key)
        entry = verify_vault(vault_file, key)
        assert isinstance(entry, SignatureEntry)

    def test_raises_on_tampered_content(self, vault_file, key):
        sign_vault(vault_file, key)
        with open(vault_file, "w") as fh:
            fh.write("tampered!")
        with pytest.raises(SignatureError, match="mismatch"):
            verify_vault(vault_file, key)

    def test_raises_on_wrong_key(self, vault_file, key):
        sign_vault(vault_file, key)
        wrong_key = generate_key()
        with pytest.raises(SignatureError):
            verify_vault(vault_file, wrong_key)

    def test_raises_when_no_sidecar(self, vault_file, key):
        with pytest.raises(SignatureError, match="No signature file"):
            verify_vault(vault_file, key)

    def test_raises_on_missing_vault_file(self, vault_file, key):
        sign_vault(vault_file, key)
        os.remove(vault_file)
        with pytest.raises(FileNotFoundError):
            verify_vault(vault_file, key)


# ---------------------------------------------------------------------------
# remove_signature
# ---------------------------------------------------------------------------

class TestRemoveSignature:
    def test_returns_true_when_removed(self, vault_file, key):
        sign_vault(vault_file, key)
        assert remove_signature(vault_file) is True

    def test_sidecar_no_longer_exists(self, vault_file, key):
        sign_vault(vault_file, key)
        remove_signature(vault_file)
        assert not os.path.isfile(_get_sig_path(vault_file))

    def test_returns_false_when_no_sidecar(self, vault_file):
        assert remove_signature(vault_file) is False
