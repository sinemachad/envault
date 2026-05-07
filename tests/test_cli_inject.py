"""Tests for envault.cli_inject."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.crypto import generate_key
from envault.vault import lock
from envault.cli_inject import cmd_inject, build_inject_subparsers
from envault.env_inject import InjectionResult


@pytest.fixture()
def vault_file(tmp_path: Path):
    key = generate_key()
    env_path = tmp_path / ".env"
    vault_path = tmp_path / ".env.vault"
    env_path.write_text("APP=test\nFOO=bar\n")
    lock(str(env_path), str(vault_path), key)
    return str(vault_path), key


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        vault=".env.vault",
        key="somekey",
        profile=None,
        overwrite=False,
        quiet=False,
        command=[],
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdInject:
    def test_prints_injected_count(self, vault_file, capsys):
        path, key = vault_file
        args = _make_args(vault=path, key=key)
        cmd_inject(args)
        out = capsys.readouterr().out
        assert "Injected" in out
        assert "2" in out

    def test_quiet_flag_suppresses_output(self, vault_file, capsys):
        path, key = vault_file
        args = _make_args(vault=path, key=key, quiet=True)
        cmd_inject(args)
        out = capsys.readouterr().out
        assert out == ""

    def test_exits_on_bad_key(self, vault_file):
        path, _ = vault_file
        args = _make_args(vault=path, key=generate_key())
        with pytest.raises(SystemExit) as exc_info:
            cmd_inject(args)
        assert exc_info.value.code == 1

    def test_runs_command_after_inject(self, vault_file):
        path, key = vault_file
        args = _make_args(vault=path, key=key, command=["true"])
        mock_proc = MagicMock(returncode=0)
        with patch("envault.cli_inject.subprocess.run", return_value=mock_proc) as mock_run:
            with pytest.raises(SystemExit) as exc_info:
                cmd_inject(args)
            mock_run.assert_called_once()
        assert exc_info.value.code == 0

    def test_build_inject_subparsers_registers_command(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_inject_subparsers(sub)
        args = parser.parse_args(
            ["inject", ".env.vault", "mykey", "--overwrite", "--quiet"]
        )
        assert args.vault == ".env.vault"
        assert args.key == "mykey"
        assert args.overwrite is True
        assert args.quiet is True
