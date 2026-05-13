"""Tests for envault.ttl — TTL / expiry support."""

from __future__ import annotations

import json
import time

import pytest

from envault.ttl import (
    TTLEntry,
    check_ttl,
    read_ttl,
    remove_ttl,
    set_ttl,
)


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "secrets.env.vault"
    p.write_text("dummy")
    return str(p)


class TestSetTTL:
    def test_returns_ttl_entry(self, vault_file):
        entry = set_ttl(vault_file, 3600)
        assert isinstance(entry, TTLEntry)

    def test_expires_at_is_in_future(self, vault_file):
        entry = set_ttl(vault_file, 3600)
        assert entry.expires_at > time.time()

    def test_seconds_remaining_close_to_ttl(self, vault_file):
        entry = set_ttl(vault_file, 3600)
        assert 3599 <= entry.seconds_remaining() <= 3600

    def test_ttl_file_written_to_disk(self, vault_file, tmp_path):
        set_ttl(vault_file, 60)
        ttl_file = tmp_path / "secrets.env.ttl"
        assert ttl_file.exists()

    def test_ttl_file_is_valid_json(self, vault_file, tmp_path):
        set_ttl(vault_file, 60)
        ttl_file = tmp_path / "secrets.env.ttl"
        data = json.loads(ttl_file.read_text())
        assert "expires_at" in data
        assert "created_at" in data

    def test_zero_seconds_raises(self, vault_file):
        with pytest.raises(ValueError):
            set_ttl(vault_file, 0)

    def test_negative_seconds_raises(self, vault_file):
        with pytest.raises(ValueError):
            set_ttl(vault_file, -10)


class TestReadTTL:
    def test_returns_none_when_no_ttl(self, vault_file):
        assert read_ttl(vault_file) is None

    def test_returns_entry_after_set(self, vault_file):
        set_ttl(vault_file, 3600)
        entry = read_ttl(vault_file)
        assert entry is not None
        assert isinstance(entry, TTLEntry)

    def test_entry_not_expired_for_future_ttl(self, vault_file):
        set_ttl(vault_file, 3600)
        entry = read_ttl(vault_file)
        assert not entry.is_expired()


class TestRemoveTTL:
    def test_returns_true_when_removed(self, vault_file):
        set_ttl(vault_file, 60)
        assert remove_ttl(vault_file) is True

    def test_returns_false_when_nothing_to_remove(self, vault_file):
        assert remove_ttl(vault_file) is False

    def test_ttl_absent_after_removal(self, vault_file):
        set_ttl(vault_file, 60)
        remove_ttl(vault_file)
        assert read_ttl(vault_file) is None


class TestCheckTTL:
    def test_returns_none_for_unexpired_ttl(self, vault_file):
        set_ttl(vault_file, 3600)
        assert check_ttl(vault_file) is None

    def test_returns_entry_for_expired_ttl(self, vault_file):
        entry = set_ttl(vault_file, 3600)
        # Manually backdate the expiry
        entry.expires_at = time.time() - 1
        import envault.ttl as ttl_mod
        ttl_path = ttl_mod._get_ttl_path(vault_file)
        import json as _json
        ttl_path.write_text(
            _json.dumps(
                {
                    "vault": entry.vault,
                    "expires_at": entry.expires_at,
                    "created_at": entry.created_at,
                }
            )
        )
        result = check_ttl(vault_file)
        assert result is not None
        assert result.is_expired()

    def test_returns_none_when_no_ttl_set(self, vault_file):
        assert check_ttl(vault_file) is None
