"""Tests for envault.diff module."""

import pytest
from envault.diff import diff_envs, format_diff, EnvDiff


OLD_ENV = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "old_secret"}
NEW_ENV = {"DB_HOST": "prod.db", "DB_PORT": "5432", "API_KEY": "abc123"}


class TestDiffEnvs:
    def test_detects_added_keys(self):
        diff = diff_envs(OLD_ENV, NEW_ENV, mask_values=False)
        assert "API_KEY" in diff.added

    def test_detects_removed_keys(self):
        diff = diff_envs(OLD_ENV, NEW_ENV, mask_values=False)
        assert "SECRET" in diff.removed

    def test_detects_changed_keys(self):
        diff = diff_envs(OLD_ENV, NEW_ENV, mask_values=False)
        assert "DB_HOST" in diff.changed
        assert diff.changed["DB_HOST"] == ("localhost", "prod.db")

    def test_detects_unchanged_keys(self):
        diff = diff_envs(OLD_ENV, NEW_ENV, mask_values=False)
        assert "DB_PORT" in diff.unchanged

    def test_identical_envs_have_no_changes(self):
        diff = diff_envs(OLD_ENV, OLD_ENV, mask_values=False)
        assert not diff.has_changes

    def test_empty_old_env(self):
        diff = diff_envs({}, {"FOO": "bar"}, mask_values=False)
        assert "FOO" in diff.added
        assert diff.has_changes

    def test_empty_new_env(self):
        diff = diff_envs({"FOO": "bar"}, {}, mask_values=False)
        assert "FOO" in diff.removed

    def test_mask_values_obscures_secrets(self):
        diff = diff_envs(OLD_ENV, NEW_ENV, mask_values=True)
        for val in diff.added.values():
            assert "***" in val
        for val in diff.removed.values():
            assert "***" in val

    def test_mask_false_shows_plain_values(self):
        diff = diff_envs(OLD_ENV, NEW_ENV, mask_values=False)
        assert diff.added["API_KEY"] == "abc123"


class TestFormatDiff:
    def test_added_lines_start_with_plus(self):
        diff = diff_envs({}, {"FOO": "bar"}, mask_values=False)
        output = format_diff(diff)
        assert output.startswith("+")

    def test_removed_lines_start_with_minus(self):
        diff = diff_envs({"FOO": "bar"}, {}, mask_values=False)
        output = format_diff(diff)
        assert output.startswith("-")

    def test_changed_lines_start_with_tilde(self):
        diff = diff_envs({"X": "1"}, {"X": "2"}, mask_values=False)
        output = format_diff(diff)
        assert output.startswith("~")

    def test_no_changes_returns_message(self):
        diff = diff_envs({"A": "1"}, {"A": "1"}, mask_values=False)
        output = format_diff(diff)
        assert output == "No changes."

    def test_full_diff_output(self):
        diff = diff_envs(OLD_ENV, NEW_ENV, mask_values=False)
        output = format_diff(diff)
        assert "API_KEY" in output
        assert "SECRET" in output
        assert "DB_HOST" in output
