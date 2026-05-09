"""Tests for envault.cli_rollback."""

from __future__ import annotations

import argparse
import sys
import pytest

from envault.crypto import generate_key
from envault.vault import lock
from envault.history import record_change
from envault.rollback import list_rollback_points
from envault.cli_rollback import cmd_rollback, cmd_rollback_list


@pytest.fixture()
def shared_key():
    return generate_key()


@pytest.fixture()
def vault_file(tmp_path, shared_key):
    path = str(tmp_path / "test.vault")
    lock({"A": "1", "B": "2"}, path, shared_key)
    return path


def _make_args(**kwargs):
    defaults = {"vault": None, "key": None, "index": 0, "quiet": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _add_snapshot(vault_path, key, action="snap"):
    from envault.vault import unlock
    env = unlock(vault_path, key)
    record_change(vault_path, action=action, snapshot=env)


class TestCmdRollbackList:
    def test_prints_no_points_message(self, vault_file, capsys):
        args = _make_args(vault=vault_file)
        cmd_rollback_list(args)
        out = capsys.readouterr().out
        assert "No rollback points" in out

    def test_lists_available_points(self, vault_file, shared_key, capsys):
        _add_snapshot(vault_file, shared_key, action="my-action")
        args = _make_args(vault=vault_file)
        cmd_rollback_list(args)
        out = capsys.readouterr().out
        assert "my-action" in out


class TestCmdRollback:
    def test_prints_success_message(self, vault_file, shared_key, capsys):
        _add_snapshot(vault_file, shared_key, action="snap")
        args = _make_args(vault=vault_file, key=shared_key)
        cmd_rollback(args)
        out = capsys.readouterr().out
        assert "Rolled back" in out

    def test_quiet_suppresses_output(self, vault_file, shared_key, capsys):
        _add_snapshot(vault_file, shared_key, action="snap")
        args = _make_args(vault=vault_file, key=shared_key, quiet=True)
        cmd_rollback(args)
        out = capsys.readouterr().out
        assert out == ""

    def test_exits_on_no_rollback_points(self, vault_file, shared_key):
        args = _make_args(vault=vault_file, key=shared_key)
        with pytest.raises(SystemExit) as exc_info:
            cmd_rollback(args)
        assert exc_info.value.code == 1

    def test_exits_on_bad_index(self, vault_file, shared_key):
        _add_snapshot(vault_file, shared_key)
        args = _make_args(vault=vault_file, key=shared_key, index=99)
        with pytest.raises(SystemExit) as exc_info:
            cmd_rollback(args)
        assert exc_info.value.code == 1
