"""Tests for envault.rotation."""

import os
import pytest
from pathlib import Path

from envault.crypto import generate_key, encrypt, decrypt
from envault.rotation import rotate_key, rotate_env_key


SAMPLE_PLAINTEXT = "DB_HOST=localhost\nDB_PASS=secret\n"


@pytest.fixture()
def vault_file(tmp_path: Path):
    key = generate_key()
    ciphertext = encrypt(SAMPLE_PLAINTEXT, key)
    vpath = tmp_path / "test.env.vault"
    vpath.write_text(ciphertext + "\n", encoding="utf-8")
    return vpath, key


class TestRotateKey:
    def test_returns_new_key_string(self, vault_file):
        vpath, old_key = vault_file
        new_key = rotate_key(str(vpath), old_key)
        assert isinstance(new_key, str)
        assert len(new_key) > 0

    def test_new_key_differs_from_old(self, vault_file):
        vpath, old_key = vault_file
        new_key = rotate_key(str(vpath), old_key)
        assert new_key != old_key

    def test_vault_decryptable_with_new_key(self, vault_file):
        vpath, old_key = vault_file
        new_key = rotate_key(str(vpath), old_key)
        plaintext = decrypt(vpath.read_text(encoding="utf-8").strip(), new_key)
        assert plaintext == SAMPLE_PLAINTEXT

    def test_vault_no_longer_decryptable_with_old_key(self, vault_file):
        vpath, old_key = vault_file
        rotate_key(str(vpath), old_key)
        with pytest.raises(Exception):
            decrypt(vpath.read_text(encoding="utf-8").strip(), old_key)

    def test_accepts_explicit_new_key(self, vault_file):
        vpath, old_key = vault_file
        explicit_key = generate_key()
        returned_key = rotate_key(str(vpath), old_key, new_key=explicit_key)
        assert returned_key == explicit_key

    def test_raises_on_bad_old_key(self, vault_file):
        vpath, _ = vault_file
        with pytest.raises(ValueError, match="Failed to decrypt"):
            rotate_key(str(vpath), generate_key())

    def test_raises_on_missing_vault(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            rotate_key(str(tmp_path / "missing.vault"), generate_key())


class TestRotateEnvKey:
    def test_accepts_plain_env_path(self, vault_file):
        vpath, old_key = vault_file
        env_path = str(vpath).replace(".vault", "")
        new_key = rotate_env_key(env_path, old_key)
        plaintext = decrypt(vpath.read_text(encoding="utf-8").strip(), new_key)
        assert plaintext == SAMPLE_PLAINTEXT

    def test_accepts_vault_path_directly(self, vault_file):
        vpath, old_key = vault_file
        new_key = rotate_env_key(str(vpath), old_key)
        assert isinstance(new_key, str)
