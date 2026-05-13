"""Tests for envault.checksum."""

import os
import pytest

from envault.checksum import (
    ChecksumEntry,
    compute_checksum,
    load_checksum,
    save_checksum,
    verify_checksum,
)


@pytest.fixture
def vault_file(tmp_path):
    p = tmp_path / "secrets.env.vault"
    p.write_bytes(b"ENCRYPTED_CONTENT_ABCDEF1234567890")
    return str(p)


class TestComputeChecksum:
    def test_returns_checksum_entry(self, vault_file):
        result = compute_checksum(vault_file)
        assert isinstance(result, ChecksumEntry)

    def test_default_algorithm_is_sha256(self, vault_file):
        result = compute_checksum(vault_file)
        assert result.algorithm == "sha256"

    def test_digest_is_hex_string(self, vault_file):
        result = compute_checksum(vault_file)
        int(result.digest, 16)  # should not raise

    def test_digest_length_for_sha256(self, vault_file):
        result = compute_checksum(vault_file)
        assert len(result.digest) == 64

    def test_supports_md5_algorithm(self, vault_file):
        result = compute_checksum(vault_file, algorithm="md5")
        assert result.algorithm == "md5"
        assert len(result.digest) == 32

    def test_raises_on_unsupported_algorithm(self, vault_file):
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            compute_checksum(vault_file, algorithm="rot13")

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            compute_checksum(str(tmp_path / "nonexistent.vault"))

    def test_different_content_yields_different_digest(self, tmp_path):
        a = tmp_path / "a.vault"
        b = tmp_path / "b.vault"
        a.write_bytes(b"content_a")
        b.write_bytes(b"content_b")
        assert compute_checksum(str(a)).digest != compute_checksum(str(b)).digest


class TestSaveAndLoadChecksum:
    def test_save_returns_path_string(self, vault_file):
        entry = compute_checksum(vault_file)
        path = save_checksum(entry)
        assert isinstance(path, str)
        assert os.path.exists(path)

    def test_checksum_file_is_json(self, vault_file):
        import json
        entry = compute_checksum(vault_file)
        path = save_checksum(entry)
        with open(path) as fh:
            data = json.load(fh)
        assert "digest" in data
        assert "algorithm" in data

    def test_load_returns_none_when_absent(self, vault_file):
        result = load_checksum(vault_file)
        assert result is None

    def test_load_returns_entry_after_save(self, vault_file):
        entry = compute_checksum(vault_file)
        save_checksum(entry)
        loaded = load_checksum(vault_file)
        assert loaded is not None
        assert loaded.digest == entry.digest
        assert loaded.algorithm == entry.algorithm


class TestVerifyChecksum:
    def test_returns_true_for_unmodified_vault(self, vault_file):
        entry = compute_checksum(vault_file)
        save_checksum(entry)
        assert verify_checksum(vault_file) is True

    def test_returns_false_after_modification(self, vault_file):
        entry = compute_checksum(vault_file)
        save_checksum(entry)
        with open(vault_file, "ab") as fh:
            fh.write(b"tampered")
        assert verify_checksum(vault_file) is False

    def test_raises_when_no_checksum_stored(self, vault_file):
        with pytest.raises(FileNotFoundError):
            verify_checksum(vault_file)
