"""Tests for envault.cli_rotation."""

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.crypto import generate_key, encrypt, decrypt
from envault.cli_rotation import cmd_rotate, build_rotation_subparsers


SAMPLE = "API_KEY=abc123\nSECRET=xyz\n"


@pytest.fixture()
def vault_file(tmp_path: Path):
    key = generate_key()
    vpath = tmp_path / ".env.vault"
    vpath.write_text(encrypt(SAMPLE, key) + "\n", encoding="utf-8")
    return vpath, key


def _make_args(vault, old_key, new_key=None, print_key=False):
    ns = argparse.Namespace()
    ns.vault = vault
    ns.old_key = old_key
    ns.new_key = new_key
    ns.print_key = print_key
    return ns


class TestCmdRotate:
    def test_prints_new_key_by_default(self, vault_file, capsys):
        vpath, old_key = vault_file
        cmd_rotate(_make_args(str(vpath), old_key))
        captured = capsys.readouterr()
        assert "New key:" in captured.out

    def test_print_key_flag_outputs_only_key(self, vault_file, capsys):
        vpath, old_key = vault_file
        cmd_rotate(_make_args(str(vpath), old_key, print_key=True))
        captured = capsys.readouterr()
        new_key = captured.out.strip()
        assert len(new_key) > 20
        assert "New key:" not in new_key

    def test_vault_re-encrypted_after_rotate(self, vault_file, capsys):
        vpath, old_key = vault_file
        cmd_rotate(_make_args(str(vpath), old_key, print_key=True))
        new_key = capsys.readouterr().out.strip()
        plaintext = decrypt(vpath.read_text(encoding="utf-8").strip(), new_key)
        assert plaintext == SAMPLE

    def test_exits_on_missing_vault(self, tmp_path):
        args = _make_args(str(tmp_path / "ghost.vault"), generate_key())
        with pytest.raises(SystemExit) as exc_info:
            cmd_rotate(args)
        assert exc_info.value.code == 1

    def test_exits_on_wrong_key(self, vault_file):
        vpath, _ = vault_file
        args = _make_args(str(vpath), generate_key())
        with pytest.raises(SystemExit) as exc_info:
            cmd_rotate(args)
        assert exc_info.value.code == 1


class TestBuildRotationSubparsers:
    def test_rotate_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_rotation_subparsers(sub)
        args = parser.parse_args(["rotate", "vault.vault", "somekey"])
        assert args.vault == "vault.vault"
        assert args.old_key == "somekey"
        assert args.new_key is None
        assert args.print_key is False
