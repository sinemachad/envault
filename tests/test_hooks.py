"""Tests for envault.hooks."""

import json
import sys
from pathlib import Path

import pytest

from envault.hooks import (
    VALID_EVENTS,
    add_hook,
    list_hooks,
    remove_hook,
    run_hooks,
)


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestAddHook:
    def test_returns_dict_with_event_and_command(self, base_dir):
        result = add_hook("post-lock", "echo locked", base_dir)
        assert result["event"] == "post-lock"
        assert result["command"] == "echo locked"

    def test_hook_persisted_to_disk(self, base_dir):
        add_hook("post-lock", "echo locked", base_dir)
        hooks_file = Path(base_dir) / ".envault-hooks.json"
        assert hooks_file.exists()
        data = json.loads(hooks_file.read_text())
        assert "echo locked" in data["post-lock"]

    def test_multiple_hooks_accumulate(self, base_dir):
        add_hook("pre-lock", "echo a", base_dir)
        add_hook("pre-lock", "echo b", base_dir)
        hooks = list_hooks(base_dir)
        assert "echo a" in hooks["pre-lock"]
        assert "echo b" in hooks["pre-lock"]

    def test_duplicate_not_added_twice(self, base_dir):
        add_hook("post-unlock", "echo x", base_dir)
        add_hook("post-unlock", "echo x", base_dir)
        hooks = list_hooks(base_dir)
        assert hooks["post-unlock"].count("echo x") == 1

    def test_raises_on_invalid_event(self, base_dir):
        with pytest.raises(ValueError, match="Unknown event"):
            add_hook("on-magic", "echo oops", base_dir)


class TestRemoveHook:
    def test_removes_existing_hook(self, base_dir):
        add_hook("post-rotate", "echo rotated", base_dir)
        remove_hook("post-rotate", "echo rotated", base_dir)
        hooks = list_hooks(base_dir)
        assert "post-rotate" not in hooks

    def test_raises_on_missing_hook(self, base_dir):
        with pytest.raises(KeyError):
            remove_hook("post-lock", "echo nope", base_dir)


class TestListHooks:
    def test_returns_empty_dict_when_no_hooks(self, base_dir):
        assert list_hooks(base_dir) == {}

    def test_returns_all_hooks(self, base_dir):
        add_hook("pre-lock", "echo pre", base_dir)
        add_hook("post-lock", "echo post", base_dir)
        hooks = list_hooks(base_dir)
        assert "pre-lock" in hooks
        assert "post-lock" in hooks


class TestRunHooks:
    def test_runs_command_and_returns_results(self, base_dir):
        add_hook("post-lock", f"{sys.executable} -c \"print('hello')\"", base_dir)
        results = run_hooks("post-lock", base_dir)
        assert len(results) == 1
        assert results[0]["returncode"] == 0
        assert results[0]["stdout"] == "hello"

    def test_returns_empty_list_for_no_hooks(self, base_dir):
        results = run_hooks("pre-lock", base_dir)
        assert results == []

    def test_captures_nonzero_returncode(self, base_dir):
        add_hook("pre-rotate", f"{sys.executable} -c \"raise SystemExit(1)\"", base_dir)
        results = run_hooks("pre-rotate", base_dir)
        assert results[0]["returncode"] == 1
