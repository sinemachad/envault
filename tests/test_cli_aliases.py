"""Tests for envault.cli_aliases."""

import argparse
import pytest
from unittest.mock import patch
from envault.cli_aliases import cmd_alias_add, cmd_alias_remove, cmd_alias_show, cmd_alias_list
from envault.aliases import add_alias


def _make_args(base_dir, **kwargs):
    defaults = {"dir": base_dir, "alias": None, "target": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestCmdAliasAdd:
    def test_prints_success_message(self, base_dir, capsys):
        args = _make_args(base_dir, alias="db", target="DATABASE_URL")
        cmd_alias_add(args)
        out = capsys.readouterr().out
        assert "db" in out
        assert "DATABASE_URL" in out

    def test_exits_on_empty_alias(self, base_dir):
        args = _make_args(base_dir, alias="", target="DATABASE_URL")
        with pytest.raises(SystemExit):
            cmd_alias_add(args)

    def test_exits_on_empty_target(self, base_dir):
        args = _make_args(base_dir, alias="db", target="")
        with pytest.raises(SystemExit):
            cmd_alias_add(args)


class TestCmdAliasRemove:
    def test_prints_removed_message(self, base_dir, capsys):
        add_alias("db", "DATABASE_URL", base_dir)
        args = _make_args(base_dir, alias="db")
        cmd_alias_remove(args)
        assert "removed" in capsys.readouterr().out.lower()

    def test_exits_when_alias_missing(self, base_dir):
        args = _make_args(base_dir, alias="ghost")
        with pytest.raises(SystemExit):
            cmd_alias_remove(args)


class TestCmdAliasShow:
    def test_prints_target(self, base_dir, capsys):
        add_alias("redis", "REDIS_URL", base_dir)
        args = _make_args(base_dir, alias="redis")
        cmd_alias_show(args)
        assert "REDIS_URL" in capsys.readouterr().out

    def test_exits_when_not_found(self, base_dir):
        args = _make_args(base_dir, alias="missing")
        with pytest.raises(SystemExit):
            cmd_alias_show(args)


class TestCmdAliasList:
    def test_prints_no_aliases_when_empty(self, base_dir, capsys):
        args = _make_args(base_dir)
        cmd_alias_list(args)
        assert "No aliases" in capsys.readouterr().out

    def test_lists_all_aliases(self, base_dir, capsys):
        add_alias("db", "DATABASE_URL", base_dir)
        add_alias("redis", "REDIS_URL", base_dir)
        args = _make_args(base_dir)
        cmd_alias_list(args)
        out = capsys.readouterr().out
        assert "db" in out
        assert "redis" in out
