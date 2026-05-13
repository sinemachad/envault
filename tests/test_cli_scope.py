"""Tests for envault.cli_scope."""

import sys
import types
import pytest

from envault.cli_scope import cmd_scope_add, cmd_scope_remove, cmd_scope_show, cmd_scope_list
from envault.scope import add_scope


def _make_args(**kwargs):
    ns = types.SimpleNamespace(base_dir=".", description="", **kwargs)
    return ns


@pytest.fixture()
def base_dir(tmp_path):
    return str(tmp_path)


class TestCmdScopeAdd:
    def test_prints_success_message(self, base_dir, capsys):
        args = _make_args(base_dir=base_dir, name="dev", vault="dev.vault")
        cmd_scope_add(args)
        out = capsys.readouterr().out
        assert "dev" in out
        assert "dev.vault" in out

    def test_prints_description_when_provided(self, base_dir, capsys):
        args = _make_args(base_dir=base_dir, name="ci", vault="ci.vault", description="CI scope")
        cmd_scope_add(args)
        out = capsys.readouterr().out
        assert "CI scope" in out

    def test_exits_on_duplicate(self, base_dir, capsys):
        add_scope(base_dir, "dev", "dev.vault")
        args = _make_args(base_dir=base_dir, name="dev", vault="other.vault")
        with pytest.raises(SystemExit):
            cmd_scope_add(args)

    def test_exits_on_empty_name(self, base_dir):
        args = _make_args(base_dir=base_dir, name="", vault="dev.vault")
        with pytest.raises(SystemExit):
            cmd_scope_add(args)


class TestCmdScopeRemove:
    def test_prints_removed_message(self, base_dir, capsys):
        add_scope(base_dir, "dev", "dev.vault")
        args = _make_args(base_dir=base_dir, name="dev")
        cmd_scope_remove(args)
        out = capsys.readouterr().out
        assert "removed" in out.lower()

    def test_exits_when_not_found(self, base_dir):
        args = _make_args(base_dir=base_dir, name="ghost")
        with pytest.raises(SystemExit):
            cmd_scope_remove(args)


class TestCmdScopeShow:
    def test_prints_scope_fields(self, base_dir, capsys):
        add_scope(base_dir, "prod", "prod.vault", description="Production")
        args = _make_args(base_dir=base_dir, name="prod")
        cmd_scope_show(args)
        out = capsys.readouterr().out
        assert "prod.vault" in out
        assert "Production" in out

    def test_exits_when_not_found(self, base_dir):
        args = _make_args(base_dir=base_dir, name="unknown")
        with pytest.raises(SystemExit):
            cmd_scope_show(args)


class TestCmdScopeList:
    def test_prints_no_scopes_message(self, base_dir, capsys):
        args = _make_args(base_dir=base_dir)
        cmd_scope_list(args)
        out = capsys.readouterr().out
        assert "No scopes" in out

    def test_lists_registered_scopes(self, base_dir, capsys):
        add_scope(base_dir, "dev", "dev.vault")
        add_scope(base_dir, "prod", "prod.vault")
        args = _make_args(base_dir=base_dir)
        cmd_scope_list(args)
        out = capsys.readouterr().out
        assert "dev" in out
        assert "prod" in out
