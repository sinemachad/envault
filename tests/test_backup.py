"""Tests for envault.backup."""

import os
import pytest

from envault.backup import (
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)
from envault.crypto import generate_key
from envault.vault import lock


@pytest.fixture()
def vault_file(tmp_path):
    env_path = tmp_path / "sample.env"
    env_path.write_text("API_KEY=secret\nDEBUG=true\n")
    key = generate_key()
    vault_path = str(tmp_path / "sample.env.vault")
    lock(str(env_path), vault_path, key)
    return vault_path, key, str(tmp_path)


class TestCreateBackup:
    def test_returns_entry_dict(self, vault_file):
        vp, _, base = vault_file
        entry = create_backup(vp, base)
        assert isinstance(entry, dict)

    def test_entry_has_required_fields(self, vault_file):
        vp, _, base = vault_file
        entry = create_backup(vp, base)
        for field in ("id", "timestamp", "label", "source", "file"):
            assert field in entry

    def test_backup_file_exists_on_disk(self, vault_file):
        vp, _, base = vault_file
        entry = create_backup(vp, base)
        assert os.path.exists(entry["file"])

    def test_label_stored_in_entry(self, vault_file):
        vp, _, base = vault_file
        entry = create_backup(vp, base, label="before-deploy")
        assert entry["label"] == "before-deploy"

    def test_raises_on_missing_vault(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            create_backup(str(tmp_path / "ghost.vault"), str(tmp_path))

    def test_multiple_backups_accumulate(self, vault_file):
        vp, _, base = vault_file
        create_backup(vp, base, label="first")
        create_backup(vp, base, label="second")
        entries = list_backups(base)
        assert len(entries) == 2


class TestListBackups:
    def test_empty_when_no_backups(self, tmp_path):
        result = list_backups(str(tmp_path))
        assert result == []

    def test_newest_first_ordering(self, vault_file):
        vp, _, base = vault_file
        create_backup(vp, base, label="a")
        create_backup(vp, base, label="b")
        entries = list_backups(base)
        assert entries[0]["label"] == "b"
        assert entries[1]["label"] == "a"


class TestRestoreBackup:
    def test_restores_file_to_destination(self, vault_file, tmp_path):
        vp, key, base = vault_file
        entry = create_backup(vp, base)
        dest = str(tmp_path / "restored.env.vault")
        restore_backup(entry["id"], dest, base)
        assert os.path.exists(dest)

    def test_raises_on_unknown_id(self, tmp_path):
        with pytest.raises(KeyError):
            restore_backup("nonexistent", str(tmp_path / "x.vault"), str(tmp_path))


class TestDeleteBackup:
    def test_removes_entry_from_index(self, vault_file):
        vp, _, base = vault_file
        entry = create_backup(vp, base)
        delete_backup(entry["id"], base)
        assert list_backups(base) == []

    def test_removes_file_from_disk(self, vault_file):
        vp, _, base = vault_file
        entry = create_backup(vp, base)
        backup_file = entry["file"]
        delete_backup(entry["id"], base)
        assert not os.path.exists(backup_file)

    def test_raises_on_unknown_id(self, tmp_path):
        with pytest.raises(KeyError):
            delete_backup("ghost", str(tmp_path))
