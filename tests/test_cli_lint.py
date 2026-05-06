"""Tests for envault.cli_lint module."""

import argparse
import sys
import textwrap
import pytest

from envault.cli_lint import cmd_lint, build_lint_subparsers


def _make_args(env_file: str, strict: bool = False) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, strict=strict)


@pytest.fixture()
def clean_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=abc123\nSECRET=xyz\n")
    return str(p)


@pytest.fixture()
def warn_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("api_key=abc123\n")
    return str(p)


@pytest.fixture()
def error_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DUPE=first\nDUPE=second\n")
    return str(p)


class TestCmdLint:
    def test_clean_file_exits_zero(self, clean_env_file, capsys):
        cmd_lint(_make_args(clean_env_file))
        captured = capsys.readouterr()
        assert "No issues found" in captured.out

    def test_warning_file_exits_zero_by_default(self, warn_env_file):
        """Warnings alone should not cause non-zero exit without --strict."""
        cmd_lint(_make_args(warn_env_file))  # should not raise SystemExit

    def test_warning_file_exits_two_with_strict(self, warn_env_file):
        with pytest.raises(SystemExit) as exc_info:
            cmd_lint(_make_args(warn_env_file, strict=True))
        assert exc_info.value.code == 2

    def test_error_file_exits_two(self, error_env_file):
        with pytest.raises(SystemExit) as exc_info:
            cmd_lint(_make_args(error_env_file))
        assert exc_info.value.code == 2

    def test_error_file_prints_code(self, error_env_file, capsys):
        with pytest.raises(SystemExit):
            cmd_lint(_make_args(error_env_file))
        captured = capsys.readouterr()
        assert "E001" in captured.out

    def test_missing_file_exits_one(self, tmp_path):
        args = _make_args(str(tmp_path / "nonexistent.env"))
        with pytest.raises(SystemExit) as exc_info:
            cmd_lint(args)
        assert exc_info.value.code == 1


class TestBuildLintSubparsers:
    def test_lint_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_lint_subparsers(sub)
        args = parser.parse_args(["lint", "some.env"])
        assert args.env_file == "some.env"

    def test_strict_flag_defaults_false(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_lint_subparsers(sub)
        args = parser.parse_args(["lint", "some.env"])
        assert args.strict is False

    def test_strict_flag_sets_true(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_lint_subparsers(sub)
        args = parser.parse_args(["lint", "--strict", "some.env"])
        assert args.strict is True
