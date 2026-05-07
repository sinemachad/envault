"""Tests for envault.history."""

import os
import pytest

from envault.history import (
    record_change,
    read_history,
    clear_history,
    format_history,
    _get_history_path,
    HISTORY_FILENAME,
)


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "secrets.vault"
    p.write_text("dummy")
    return str(p)


# ---------------------------------------------------------------------------
# record_change
# ---------------------------------------------------------------------------

class TestRecordChange:
    def test_returns_dict(self, vault_file):
        entry = record_change(vault_file, "lock")
        assert isinstance(entry, dict)

    def test_entry_has_required_fields(self, vault_file):
        entry = record_change(vault_file, "lock")
        assert "timestamp" in entry
        assert "vault" in entry
        assert "action" in entry

    def test_action_stored_correctly(self, vault_file):
        entry = record_change(vault_file, "rotate")
        assert entry["action"] == "rotate"

    def test_actor_stored_when_provided(self, vault_file):
        entry = record_change(vault_file, "unlock", actor="alice")
        assert entry["actor"] == "alice"

    def test_note_stored_when_provided(self, vault_file):
        entry = record_change(vault_file, "lock", note="nightly job")
        assert entry["note"] == "nightly job"

    def test_empty_action_raises(self, vault_file):
        with pytest.raises(ValueError):
            record_change(vault_file, "")

    def test_history_file_created(self, vault_file, tmp_path):
        record_change(vault_file, "lock")
        history_path = tmp_path / HISTORY_FILENAME
        assert history_path.exists()

    def test_multiple_entries_accumulate(self, vault_file):
        record_change(vault_file, "lock")
        record_change(vault_file, "unlock")
        entries = read_history(vault_file)
        assert len(entries) == 2


# ---------------------------------------------------------------------------
# read_history
# ---------------------------------------------------------------------------

class TestReadHistory:
    def test_returns_empty_list_for_new_vault(self, vault_file):
        entries = read_history(vault_file)
        assert entries == []

    def test_returns_all_recorded_entries(self, vault_file):
        for action in ("lock", "unlock", "rotate"):
            record_change(vault_file, action)
        entries = read_history(vault_file)
        assert [e["action"] for e in entries] == ["lock", "unlock", "rotate"]


# ---------------------------------------------------------------------------
# clear_history
# ---------------------------------------------------------------------------

class TestClearHistory:
    def test_returns_count_of_removed_entries(self, vault_file):
        record_change(vault_file, "lock")
        record_change(vault_file, "unlock")
        count = clear_history(vault_file)
        assert count == 2

    def test_history_empty_after_clear(self, vault_file):
        record_change(vault_file, "lock")
        clear_history(vault_file)
        assert read_history(vault_file) == []

    def test_clear_on_empty_returns_zero(self, vault_file):
        assert clear_history(vault_file) == 0


# ---------------------------------------------------------------------------
# format_history
# ---------------------------------------------------------------------------

class TestFormatHistory:
    def test_empty_returns_placeholder(self):
        assert format_history([]) == "(no history)"

    def test_contains_action(self, vault_file):
        entry = record_change(vault_file, "lock")
        output = format_history([entry])
        assert "lock" in output

    def test_contains_actor_when_present(self, vault_file):
        entry = record_change(vault_file, "rotate", actor="bob")
        output = format_history([entry])
        assert "bob" in output

    def test_each_entry_on_own_line(self, vault_file):
        record_change(vault_file, "lock")
        record_change(vault_file, "unlock")
        entries = read_history(vault_file)
        output = format_history(entries)
        assert output.count("\n") == 1  # two lines → one newline
