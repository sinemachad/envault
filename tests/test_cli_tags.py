"""Tests for envault.cli_tags module."""
import argparse
import pytest
from unittest.mock import patch, MagicMock
from envault.cli_tags import cmd_tag_add, cmd_tag_remove, cmd_tag_list, cmd_tag_find, build_tag_subparsers


def _make_args(**kwargs):
    args = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(args, k, v)
    return args


class TestCmdTagAdd:
    def test_prints_success_message(self, capsys):
        with patch("envault.cli_tags.add_tag", return_value={"vault_file": "s.vault", "tags": ["prod"]}):
            cmd_tag_add(_make_args(vault_file="s.vault", tag="prod"))
        out = capsys.readouterr().out
        assert "Tagged" in out
        assert "prod" in out

    def test_prints_current_tags(self, capsys):
        with patch("envault.cli_tags.add_tag", return_value={"vault_file": "s.vault", "tags": ["prod", "backend"]}):
            cmd_tag_add(_make_args(vault_file="s.vault", tag="backend"))
        out = capsys.readouterr().out
        assert "backend" in out

    def test_exits_on_error(self):
        with patch("envault.cli_tags.add_tag", side_effect=Exception("fail")):
            with pytest.raises(SystemExit):
                cmd_tag_add(_make_args(vault_file="s.vault", tag="prod"))


class TestCmdTagRemove:
    def test_prints_removal_message(self, capsys):
        with patch("envault.cli_tags.remove_tag", return_value={"vault_file": "s.vault", "tags": []}):
            cmd_tag_remove(_make_args(vault_file="s.vault", tag="prod"))
        out = capsys.readouterr().out
        assert "Removed" in out

    def test_shows_no_tags_remaining(self, capsys):
        with patch("envault.cli_tags.remove_tag", return_value={"vault_file": "s.vault", "tags": []}):
            cmd_tag_remove(_make_args(vault_file="s.vault", tag="prod"))
        out = capsys.readouterr().out
        assert "No tags remaining" in out

    def test_exits_on_value_error(self):
        with patch("envault.cli_tags.remove_tag", side_effect=ValueError("Tag 'x' not found")):
            with pytest.raises(SystemExit):
                cmd_tag_remove(_make_args(vault_file="s.vault", tag="x"))


class TestCmdTagList:
    def test_prints_tags_when_present(self, capsys):
        with patch("envault.cli_tags.list_tags", return_value=["staging", "frontend"]):
            cmd_tag_list(_make_args(vault_file="s.vault"))
        out = capsys.readouterr().out
        assert "staging" in out
        assert "frontend" in out

    def test_prints_no_tags_message(self, capsys):
        with patch("envault.cli_tags.list_tags", return_value=[]):
            cmd_tag_list(_make_args(vault_file="s.vault"))
        out = capsys.readouterr().out
        assert "No tags found" in out


class TestCmdTagFind:
    def test_prints_matching_vault_files(self, capsys):
        with patch("envault.cli_tags.find_by_tag", return_value=["a.vault", "b.vault"]):
            cmd_tag_find(_make_args(tag="production"))
        out = capsys.readouterr().out
        assert "a.vault" in out
        assert "b.vault" in out

    def test_prints_not_found_message(self, capsys):
        with patch("envault.cli_tags.find_by_tag", return_value=[]):
            cmd_tag_find(_make_args(tag="ghost"))
        out = capsys.readouterr().out
        assert "No vault files found" in out


class TestBuildTagSubparsers:
    def test_registers_tag_subcommand(self):
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")
        build_tag_subparsers(subs)
        args = parser.parse_args(["tag", "list", "secrets.vault"])
        assert args.vault_file == "secrets.vault"
