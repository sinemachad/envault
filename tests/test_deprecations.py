"""Tests for envault.deprecations."""

import json
import os
import pytest

from envault.deprecations import (
    DeprecationEntry,
    add_deprecation,
    check_env_deprecations,
    list_deprecations,
    remove_deprecation,
)


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestAddDeprecation:
    def test_returns_deprecation_entry(self, base_dir):
        entry = add_deprecation("OLD_KEY", "Use NEW_KEY instead", base_dir=base_dir)
        assert isinstance(entry, DeprecationEntry)

    def test_entry_has_correct_key(self, base_dir):
        entry = add_deprecation("OLD_KEY", "reason", base_dir=base_dir)
        assert entry.key == "OLD_KEY"

    def test_entry_has_reason(self, base_dir):
        entry = add_deprecation("OLD_KEY", "legacy field", base_dir=base_dir)
        assert entry.reason == "legacy field"

    def test_replacement_stored(self, base_dir):
        entry = add_deprecation("OLD_KEY", "r", base_dir=base_dir, replacement="NEW_KEY")
        assert entry.replacement == "NEW_KEY"

    def test_since_stored(self, base_dir):
        entry = add_deprecation("OLD_KEY", "r", base_dir=base_dir, since="1.2.0")
        assert entry.since == "1.2.0"

    def test_persisted_to_disk(self, base_dir):
        add_deprecation("OLD_KEY", "reason", base_dir=base_dir)
        index_path = os.path.join(base_dir, ".envault", "deprecations.json")
        assert os.path.exists(index_path)
        with open(index_path) as f:
            data = json.load(f)
        assert "OLD_KEY" in data

    def test_multiple_keys_accumulate(self, base_dir):
        add_deprecation("KEY_A", "reason a", base_dir=base_dir)
        add_deprecation("KEY_B", "reason b", base_dir=base_dir)
        entries = list_deprecations(base_dir=base_dir)
        keys = [e.key for e in entries]
        assert "KEY_A" in keys
        assert "KEY_B" in keys

    def test_overwrite_existing_key(self, base_dir):
        add_deprecation("OLD_KEY", "first reason", base_dir=base_dir)
        add_deprecation("OLD_KEY", "updated reason", base_dir=base_dir)
        entries = list_deprecations(base_dir=base_dir)
        matches = [e for e in entries if e.key == "OLD_KEY"]
        assert len(matches) == 1
        assert matches[0].reason == "updated reason"


class TestRemoveDeprecation:
    def test_returns_true_when_removed(self, base_dir):
        add_deprecation("OLD_KEY", "reason", base_dir=base_dir)
        result = remove_deprecation("OLD_KEY", base_dir=base_dir)
        assert result is True

    def test_returns_false_when_not_found(self, base_dir):
        result = remove_deprecation("NONEXISTENT", base_dir=base_dir)
        assert result is False

    def test_entry_no_longer_listed(self, base_dir):
        add_deprecation("OLD_KEY", "reason", base_dir=base_dir)
        remove_deprecation("OLD_KEY", base_dir=base_dir)
        entries = list_deprecations(base_dir=base_dir)
        assert all(e.key != "OLD_KEY" for e in entries)


class TestCheckEnvDeprecations:
    def test_returns_empty_when_no_matches(self, base_dir):
        add_deprecation("OLD_KEY", "reason", base_dir=base_dir)
        hits = check_env_deprecations({"UNRELATED": "val"}, base_dir=base_dir)
        assert hits == []

    def test_returns_entry_for_matching_key(self, base_dir):
        add_deprecation("OLD_KEY", "use NEW", base_dir=base_dir, replacement="NEW_KEY")
        hits = check_env_deprecations({"OLD_KEY": "value"}, base_dir=base_dir)
        assert len(hits) == 1
        assert hits[0].key == "OLD_KEY"
        assert hits[0].replacement == "NEW_KEY"

    def test_returns_multiple_hits(self, base_dir):
        add_deprecation("KEY_A", "r", base_dir=base_dir)
        add_deprecation("KEY_B", "r", base_dir=base_dir)
        hits = check_env_deprecations(
            {"KEY_A": "1", "KEY_B": "2", "KEY_C": "3"}, base_dir=base_dir
        )
        assert len(hits) == 2
