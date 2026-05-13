"""Tests for envault.expiry."""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from envault.expiry import (
    ExpiryEntry,
    set_expiry,
    get_expiry,
    remove_expiry,
    list_expiries,
)


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "secrets.env.vault"
    p.write_text("dummy")
    return str(p)


@pytest.fixture()
def base_dir(tmp_path):
    return str(tmp_path)


def _future(days: int = 30) -> str:
    dt = datetime.now(tz=timezone.utc) + timedelta(days=days)
    return dt.isoformat()


def _past(days: int = 1) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days)
    return dt.isoformat()


class TestSetExpiry:
    def test_returns_expiry_entry(self, vault_file, base_dir):
        entry = set_expiry(vault_file, _future(), base_dir=base_dir)
        assert isinstance(entry, ExpiryEntry)

    def test_entry_has_correct_vault(self, vault_file, base_dir):
        entry = set_expiry(vault_file, _future(), base_dir=base_dir)
        assert entry.vault == vault_file

    def test_entry_has_correct_expires_at(self, vault_file, base_dir):
        ts = _future(60)
        entry = set_expiry(vault_file, ts, base_dir=base_dir)
        assert entry.expires_at == ts

    def test_note_stored(self, vault_file, base_dir):
        entry = set_expiry(vault_file, _future(), note="rotate soon", base_dir=base_dir)
        assert entry.note == "rotate soon"

    def test_persisted_to_disk(self, vault_file, base_dir):
        set_expiry(vault_file, _future(), base_dir=base_dir)
        loaded = get_expiry(vault_file, base_dir=base_dir)
        assert loaded is not None
        assert loaded.vault == vault_file

    def test_invalid_date_raises(self, vault_file, base_dir):
        with pytest.raises(ValueError):
            set_expiry(vault_file, "not-a-date", base_dir=base_dir)


class TestGetExpiry:
    def test_returns_none_when_not_set(self, vault_file, base_dir):
        result = get_expiry(vault_file, base_dir=base_dir)
        assert result is None

    def test_returns_entry_after_set(self, vault_file, base_dir):
        set_expiry(vault_file, _future(), base_dir=base_dir)
        result = get_expiry(vault_file, base_dir=base_dir)
        assert isinstance(result, ExpiryEntry)


class TestExpiryEntry:
    def test_not_expired_for_future_date(self, vault_file, base_dir):
        entry = set_expiry(vault_file, _future(10), base_dir=base_dir)
        assert not entry.is_expired()

    def test_expired_for_past_date(self, vault_file, base_dir):
        entry = set_expiry(vault_file, _past(1), base_dir=base_dir)
        assert entry.is_expired()

    def test_days_remaining_positive_for_future(self, vault_file, base_dir):
        entry = set_expiry(vault_file, _future(5), base_dir=base_dir)
        assert entry.days_remaining() >= 4

    def test_days_remaining_zero_when_expired(self, vault_file, base_dir):
        entry = set_expiry(vault_file, _past(2), base_dir=base_dir)
        assert entry.days_remaining() == 0

    def test_repr_contains_vault(self, vault_file, base_dir):
        entry = set_expiry(vault_file, _future(), base_dir=base_dir)
        assert vault_file in repr(entry)


class TestRemoveExpiry:
    def test_returns_true_when_removed(self, vault_file, base_dir):
        set_expiry(vault_file, _future(), base_dir=base_dir)
        assert remove_expiry(vault_file, base_dir=base_dir) is True

    def test_returns_false_when_not_present(self, vault_file, base_dir):
        assert remove_expiry(vault_file, base_dir=base_dir) is False

    def test_entry_gone_after_remove(self, vault_file, base_dir):
        set_expiry(vault_file, _future(), base_dir=base_dir)
        remove_expiry(vault_file, base_dir=base_dir)
        assert get_expiry(vault_file, base_dir=base_dir) is None


class TestListExpiries:
    def test_empty_list_when_none_set(self, base_dir):
        assert list_expiries(base_dir) == []

    def test_lists_all_entries(self, tmp_path, base_dir):
        v1 = str(tmp_path / "a.vault")
        v2 = str(tmp_path / "b.vault")
        set_expiry(v1, _future(10), base_dir=base_dir)
        set_expiry(v2, _future(20), base_dir=base_dir)
        entries = list_expiries(base_dir)
        assert len(entries) == 2
        vaults = {e.vault for e in entries}
        assert v1 in vaults and v2 in vaults
