"""Tests for envault.cli_access module."""

import argparse
import pytest

from envault.access import set_allowed_keys
from envault.cli_access import (
    cmd_access_set,
    cmd_access_remove,
    cmd_access_show,
    cmd_access_list,
)


def _make_args(**kwargs):
    defaults = {"base_dir": "", "profile": "dev", "keys": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestCmdAccessSet:
    def test_prints_policy_on_success(self, base_dir, capsys):
        args = _make_args(base_dir=base_dir, profile="dev", keys="DB_URL,SECRET")
        cmd_access_set(args)
        out = capsys.readouterr().out
        assert "dev" in out
        assert "DB_URL" in out
        assert "SECRET" in out

    def test_exits_on_empty_keys(self, base_dir):
        args = _make_args(base_dir=base_dir, profile="dev", keys="   ")
        with pytest.raises(SystemExit):
            cmd_access_set(args)

    def test_overwrites_existing_policy(self, base_dir, capsys):
        """Setting keys for an existing profile should replace the previous policy."""
        set_allowed_keys(base_dir, "dev", ["OLD_KEY"])
        args = _make_args(base_dir=base_dir, profile="dev", keys="NEW_KEY")
        cmd_access_set(args)
        out = capsys.readouterr().out
        assert "NEW_KEY" in out
        assert "OLD_KEY" not in out


class TestCmdAccessRemove:
    def test_prints_success_when_removed(self, base_dir, capsys):
        set_allowed_keys(base_dir, "dev", ["X"])
        args = _make_args(base_dir=base_dir, profile="dev")
        cmd_access_remove(args)
        out = capsys.readouterr().out
        assert "removed" in out.lower()

    def test_exits_when_not_found(self, base_dir):
        args = _make_args(base_dir=base_dir, profile="ghost")
        with pytest.raises(SystemExit):
            cmd_access_remove(args)


class TestCmdAccessShow:
    def test_shows_keys_when_policy_exists(self, base_dir, capsys):
        set_allowed_keys(base_dir, "ci", ["CI_KEY"])
        args = _make_args(base_dir=base_dir, profile="ci")
        cmd_access_show(args)
        out = capsys.readouterr().out
        assert "CI_KEY" in out

    def test_shows_all_allowed_message_when_no_policy(self, base_dir, capsys):
        args = _make_args(base_dir=base_dir, profile="nobody")
        cmd_access_show(args)
        out = capsys.readouterr().out
        assert "all keys allowed" in out.lower()


class TestCmdAccessList:
    def test_prints_no_policies_when_empty(self, base_dir, capsys):
        args = _make_args(base_dir=base_dir)
        cmd_access_list(args)
        out = capsys.readouterr().out
        assert "No access policies" in out

    def test_lists_all_profiles(self, base_dir, capsys):
        set_allowed_keys(base_dir, "dev", ["A"])
        set_allowed_keys(base_dir, "prod", ["B"])
        args = _make_args(base_dir=base_dir)
        cmd_access_list(args)
        out = capsys.readouterr().out
        assert "dev" in out
        assert "prod" in out
