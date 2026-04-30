"""Tests for envault.snapshots module."""

import os
import pytest

from envault.crypto import generate_key
from envault.vault import lock
from envault.snapshots import (
    save_snapshot,
    restore_snapshot,
    list_snapshots,
    delete_snapshot,
)


@pytest.fixture
def tmp_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=secret123\nDEBUG=true\n")
    return str(env_file)


@pytest.fixture
def vault_file(tmp_path, tmp_env):
    key = generate_key()
    vault_path = str(tmp_path / ".env.vault")
    lock(tmp_env, vault_path, key)
    return vault_path, key


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path / "envault_home")


class TestSaveSnapshot:
    def test_returns_entry_dict(self, vault_file, base_dir):
        vault_path, key = vault_file
        entry = save_snapshot("v1", vault_path, key, base_dir=base_dir)
        assert isinstance(entry, dict)

    def test_entry_has_required_fields(self, vault_file, base_dir):
        vault_path, key = vault_file
        entry = save_snapshot("v1", vault_path, key, base_dir=base_dir)
        assert "name" in entry
        assert "vault_path" in entry
        assert "snapshot_file" in entry
        assert "created_at" in entry

    def test_snapshot_file_created(self, vault_file, base_dir):
        vault_path, key = vault_file
        entry = save_snapshot("v1", vault_path, key, base_dir=base_dir)
        assert os.path.exists(entry["snapshot_file"])

    def test_missing_vault_raises(self, tmp_path, base_dir):
        key = generate_key()
        with pytest.raises(FileNotFoundError):
            save_snapshot("v1", str(tmp_path / "missing.vault"), key, base_dir=base_dir)

    def test_wrong_key_raises(self, vault_file, base_dir):
        vault_path, _ = vault_file
        bad_key = generate_key()
        with pytest.raises(Exception):
            save_snapshot("v1", vault_path, bad_key, base_dir=base_dir)


class TestRestoreSnapshot:
    def test_restores_content(self, vault_file, tmp_path, base_dir):
        vault_path, key = vault_file
        save_snapshot("v1", vault_path, key, base_dir=base_dir)

        new_vault = str(tmp_path / "restored.vault")
        restore_snapshot("v1", new_vault, key, base_dir=base_dir)
        assert os.path.exists(new_vault)

    def test_missing_snapshot_raises(self, base_dir, tmp_path):
        with pytest.raises(KeyError):
            restore_snapshot("nonexistent", str(tmp_path / "x.vault"), generate_key(), base_dir=base_dir)


class TestListSnapshots:
    def test_returns_list(self, base_dir):
        assert isinstance(list_snapshots(base_dir=base_dir), list)

    def test_lists_saved_snapshots(self, vault_file, base_dir):
        vault_path, key = vault_file
        save_snapshot("alpha", vault_path, key, base_dir=base_dir)
        save_snapshot("beta", vault_path, key, base_dir=base_dir)
        names = [e["name"] for e in list_snapshots(base_dir=base_dir)]
        assert "alpha" in names
        assert "beta" in names

    def test_sorted_by_created_at(self, vault_file, base_dir):
        vault_path, key = vault_file
        save_snapshot("first", vault_path, key, base_dir=base_dir)
        save_snapshot("second", vault_path, key, base_dir=base_dir)
        entries = list_snapshots(base_dir=base_dir)
        times = [e["created_at"] for e in entries]
        assert times == sorted(times)


class TestDeleteSnapshot:
    def test_removes_from_list(self, vault_file, base_dir):
        vault_path, key = vault_file
        save_snapshot("to_delete", vault_path, key, base_dir=base_dir)
        delete_snapshot("to_delete", base_dir=base_dir)
        names = [e["name"] for e in list_snapshots(base_dir=base_dir)]
        assert "to_delete" not in names

    def test_removes_snapshot_file(self, vault_file, base_dir):
        vault_path, key = vault_file
        entry = save_snapshot("to_delete", vault_path, key, base_dir=base_dir)
        delete_snapshot("to_delete", base_dir=base_dir)
        assert not os.path.exists(entry["snapshot_file"])

    def test_missing_snapshot_raises(self, base_dir):
        with pytest.raises(KeyError):
            delete_snapshot("ghost", base_dir=base_dir)
