"""Tests for envault.cli_export."""

import argparse
import json
import os
import pytest

from envault.vault import lock
from envault.crypto import generate_key
from envault.cli_export import cmd_export, build_export_subparsers


@pytest.fixture()
def vault_file(tmp_path):
    key = generate_key()
    env_path = tmp_path / ".env"
    vault_path = tmp_path / ".env.vault"
    env_path.write_text("API_KEY=abc123\nDB_URL=postgres://localhost/db\n")
    lock(str(env_path), str(vault_path), key)
    return vault_path, key


def _make_args(**kwargs):
    defaults = dict(format="dotenv", output=None, keys=None, quiet=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdExport:
    def test_prints_dotenv_to_stdout(self, vault_file, capsys):
        vpath, key = vault_file
        args = _make_args(vault=str(vpath), key=key)
        cmd_export(args)
        out = capsys.readouterr().out
        assert "API_KEY=abc123" in out

    def test_json_format_to_stdout(self, vault_file, capsys):
        vpath, key = vault_file
        args = _make_args(vault=str(vpath), key=key, format="json")
        cmd_export(args)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["API_KEY"] == "abc123"

    def test_shell_format_contains_export(self, vault_file, capsys):
        vpath, key = vault_file
        args = _make_args(vault=str(vpath), key=key, format="shell")
        cmd_export(args)
        out = capsys.readouterr().out
        assert "export API_KEY=abc123" in out

    def test_writes_to_output_file(self, vault_file, tmp_path, capsys):
        vpath, key = vault_file
        out_file = tmp_path / "out.env"
        args = _make_args(vault=str(vpath), key=key, output=str(out_file))
        cmd_export(args)
        assert out_file.exists()
        content = out_file.read_text()
        assert "API_KEY=abc123" in content

    def test_output_file_prints_summary(self, vault_file, tmp_path, capsys):
        vpath, key = vault_file
        out_file = tmp_path / "out.env"
        args = _make_args(vault=str(vpath), key=key, output=str(out_file))
        cmd_export(args)
        out = capsys.readouterr().out
        assert "Exported" in out

    def test_quiet_suppresses_summary(self, vault_file, tmp_path, capsys):
        vpath, key = vault_file
        out_file = tmp_path / "out.env"
        args = _make_args(vault=str(vpath), key=key, output=str(out_file), quiet=True)
        cmd_export(args)
        out = capsys.readouterr().out
        assert out.strip() == ""

    def test_key_filter_limits_output(self, vault_file, capsys):
        vpath, key = vault_file
        args = _make_args(vault=str(vpath), key=key, keys=["API_KEY"])
        cmd_export(args)
        out = capsys.readouterr().out
        assert "API_KEY" in out
        assert "DB_URL" not in out

    def test_bad_key_exits_with_error(self, vault_file, capsys):
        vpath, _ = vault_file
        args = _make_args(vault=str(vpath), key="bad-key")
        with pytest.raises(SystemExit) as exc_info:
            cmd_export(args)
        assert exc_info.value.code == 1

    def test_build_sharing_subparsers_registers_export(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_export_subparsers(sub)
        args = parser.parse_args(["export", "vault.enc", "--key", "k"])
        assert args.format == "dotenv"
