"""Tests for envault.notify."""

import json
import os
from pathlib import Path

import pytest

from envault.notify import (
    NotifyEntry,
    add_notify,
    dispatch_notify,
    list_notify,
    remove_notify,
)


@pytest.fixture()
def base_dir(tmp_path):
    return str(tmp_path)


class TestAddNotify:
    def test_returns_notify_entry(self, base_dir):
        entry = add_notify(base_dir, "lock", "stdout", "")
        assert isinstance(entry, NotifyEntry)

    def test_entry_has_correct_fields(self, base_dir):
        entry = add_notify(base_dir, "unlock", "file", "/tmp/log.txt")
        assert entry.event == "unlock"
        assert entry.channel == "file"
        assert entry.target == "/tmp/log.txt"

    def test_persisted_to_disk(self, base_dir):
        add_notify(base_dir, "rotate", "stdout", "")
        notify_file = Path(base_dir) / ".envault" / "notify.json"
        assert notify_file.exists()
        data = json.loads(notify_file.read_text())
        assert "rotate" in data

    def test_multiple_entries_accumulate(self, base_dir):
        add_notify(base_dir, "lock", "stdout", "")
        add_notify(base_dir, "lock", "file", "/tmp/a.log")
        data = list_notify(base_dir, event="lock")
        assert len(data["lock"]) == 2

    def test_invalid_channel_raises(self, base_dir):
        with pytest.raises(ValueError, match="Unknown channel"):
            add_notify(base_dir, "lock", "webhook", "http://example.com")


class TestRemoveNotify:
    def test_returns_true_when_removed(self, base_dir):
        add_notify(base_dir, "lock", "stdout", "")
        result = remove_notify(base_dir, "lock", "stdout", "")
        assert result is True

    def test_returns_false_when_not_found(self, base_dir):
        result = remove_notify(base_dir, "lock", "stdout", "")
        assert result is False

    def test_entry_gone_after_removal(self, base_dir):
        add_notify(base_dir, "lock", "file", "/tmp/x.log")
        remove_notify(base_dir, "lock", "file", "/tmp/x.log")
        data = list_notify(base_dir, event="lock")
        assert data["lock"] == []


class TestListNotify:
    def test_returns_empty_dict_when_none(self, base_dir):
        data = list_notify(base_dir)
        assert data == {}

    def test_filters_by_event(self, base_dir):
        add_notify(base_dir, "lock", "stdout", "")
        add_notify(base_dir, "unlock", "stdout", "")
        data = list_notify(base_dir, event="lock")
        assert "lock" in data
        assert "unlock" not in data


class TestDispatchNotify:
    def test_returns_empty_list_when_no_entries(self, base_dir):
        outcomes = dispatch_notify(base_dir, "lock", "vault locked")
        assert outcomes == []

    def test_stdout_channel_returns_outcome(self, base_dir):
        add_notify(base_dir, "lock", "stdout", "")
        outcomes = dispatch_notify(base_dir, "lock", "vault locked")
        assert outcomes == ["stdout"]

    def test_file_channel_writes_to_file(self, base_dir, tmp_path):
        log_file = str(tmp_path / "events.log")
        add_notify(base_dir, "rotate", "file", log_file)
        dispatch_notify(base_dir, "rotate", "key rotated")
        content = Path(log_file).read_text()
        assert "rotate: key rotated" in content

    def test_file_channel_outcome_contains_ok(self, base_dir, tmp_path):
        log_file = str(tmp_path / "out.log")
        add_notify(base_dir, "unlock", "file", log_file)
        outcomes = dispatch_notify(base_dir, "unlock", "unlocked")
        assert any("file:ok" in o for o in outcomes)

    def test_command_sets_env_vars(self, base_dir, tmp_path):
        marker = str(tmp_path / "marker.txt")
        cmd = f"echo $ENVAULT_EVENT > {marker}"
        add_notify(base_dir, "lock", "command", cmd)
        dispatch_notify(base_dir, "lock", "locked")
        assert Path(marker).exists()
