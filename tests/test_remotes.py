"""Tests for envault.remotes."""

import json
import pytest
from pathlib import Path
from envault.remotes import add_remote, remove_remote, get_remote, list_remotes


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestAddRemote:
    def test_returns_entry_dict(self, base_dir):
        entry = add_remote("prod", "https://vault.example.com/prod", base_dir)
        assert entry["name"] == "prod"
        assert entry["url"] == "https://vault.example.com/prod"

    def test_remote_persisted_to_disk(self, base_dir):
        add_remote("staging", "s3://my-bucket/staging", base_dir)
        remotes_file = Path(base_dir) / "remotes.json"
        data = json.loads(remotes_file.read_text())
        assert "staging" in data
        assert data["staging"]["url"] == "s3://my-bucket/staging"

    def test_multiple_remotes_accumulate(self, base_dir):
        add_remote("alpha", "https://vault.example.com/alpha", base_dir)
        add_remote("beta", "https://vault.example.com/beta", base_dir)
        remotes = list_remotes(base_dir)
        names = [r["name"] for r in remotes]
        assert "alpha" in names
        assert "beta" in names

    def test_overwrite_existing_remote(self, base_dir):
        add_remote("prod", "https://old.example.com", base_dir)
        add_remote("prod", "https://new.example.com", base_dir)
        entry = get_remote("prod", base_dir)
        assert entry["url"] == "https://new.example.com"

    def test_invalid_name_raises(self, base_dir):
        with pytest.raises(ValueError, match="Invalid remote name"):
            add_remote("bad name!", "https://vault.example.com", base_dir)

    def test_unsupported_scheme_raises(self, base_dir):
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            add_remote("ftp_remote", "ftp://example.com/vault", base_dir)

    def test_file_scheme_allowed(self, base_dir):
        entry = add_remote("local", "file:///tmp/vault", base_dir)
        assert entry["url"] == "file:///tmp/vault"


class TestRemoveRemote:
    def test_removes_existing_remote(self, base_dir):
        add_remote("dev", "https://vault.example.com/dev", base_dir)
        remove_remote("dev", base_dir)
        assert all(r["name"] != "dev" for r in list_remotes(base_dir))

    def test_raises_on_missing_remote(self, base_dir):
        with pytest.raises(KeyError, match="Remote not found"):
            remove_remote("nonexistent", base_dir)


class TestGetRemote:
    def test_returns_correct_entry(self, base_dir):
        add_remote("qa", "https://vault.example.com/qa", base_dir)
        entry = get_remote("qa", base_dir)
        assert entry["name"] == "qa"

    def test_raises_on_missing_remote(self, base_dir):
        with pytest.raises(KeyError):
            get_remote("ghost", base_dir)


class TestListRemotes:
    def test_returns_empty_list_when_none(self, base_dir):
        assert list_remotes(base_dir) == []

    def test_returns_all_remotes(self, base_dir):
        add_remote("r1", "https://vault.example.com/r1", base_dir)
        add_remote("r2", "https://vault.example.com/r2", base_dir)
        result = list_remotes(base_dir)
        assert len(result) == 2
