"""Tests for envault.cli_compare."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.crypto import generate_key
from envault.vault import lock
from envault.cli_compare import cmd_compare, build_compare_subparsers


@pytest.fixture()
def shared_key():
    return generate_key()


def _make_vault(tmp_path: Path, env: dict, key: str, name: str) -> str:
    path = tmp_path / name
    env_text = "\n".join(f"{k}={v}" for k, v in env.items())
    path.write_text(lock(env_text, key))
    return str(path)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "left_key": None,
        "right_key": None,
        "show_values": False,
        "exit_code": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdCompare:
    def test_prints_output(self, tmp_path, shared_key, capsys):
        left = _make_vault(tmp_path, {"A": "1"}, shared_key, "l.enc")
        right = _make_vault(tmp_path, {"A": "1"}, shared_key, "r.enc")
        args = _make_args(left=left, right=right, key=shared_key)
        cmd_compare(args)
        out = capsys.readouterr().out
        assert "Comparing" in out

    def test_no_diff_message_when_identical(self, tmp_path, shared_key, capsys):
        left = _make_vault(tmp_path, {"X": "1"}, shared_key, "l.enc")
        right = _make_vault(tmp_path, {"X": "1"}, shared_key, "r.enc")
        args = _make_args(left=left, right=right, key=shared_key)
        cmd_compare(args)
        out = capsys.readouterr().out
        assert "No differences found" in out

    def test_exit_code_zero_when_no_diff(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"A": "1"}, shared_key, "l.enc")
        right = _make_vault(tmp_path, {"A": "1"}, shared_key, "r.enc")
        args = _make_args(left=left, right=right, key=shared_key, exit_code=True)
        cmd_compare(args)  # should not raise SystemExit

    def test_exit_code_one_when_diff_and_flag_set(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"A": "1"}, shared_key, "l.enc")
        right = _make_vault(tmp_path, {"B": "2"}, shared_key, "r.enc")
        args = _make_args(left=left, right=right, key=shared_key, exit_code=True)
        with pytest.raises(SystemExit) as exc_info:
            cmd_compare(args)
        assert exc_info.value.code == 1

    def test_bad_path_exits_with_error(self, tmp_path, shared_key, capsys):
        args = _make_args(left="/no/such/file.enc", right="/no/such/file2.enc", key=shared_key)
        with pytest.raises(SystemExit) as exc_info:
            cmd_compare(args)
        assert exc_info.value.code == 1
        assert "error" in capsys.readouterr().err


class TestBuildCompareSubparsers:
    def test_subparser_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_compare_subparsers(sub)
        args = parser.parse_args([])
        # Just verify the subparser was added without error

    def test_compare_subcommand_has_func(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        build_compare_subparsers(sub)
        args = parser.parse_args(["compare", "l.enc", "r.enc", "--key", "somekey"])
        assert args.func is cmd_compare
        assert args.left == "l.enc"
        assert args.right == "r.enc"
