"""Tests for envault.cli module."""

import pytest
from pathlib import Path

from envault.cli import main, build_parser
from envault.crypto import generate_key


class TestKeygen:
    def test_keygen_prints_key(self, capsys):
        rc = main(["keygen"])
        captured = capsys.readouterr()
        assert rc == 0
        assert len(captured.out.strip()) > 20

    def test_keygen_output_is_unique(self, capsys):
        main(["keygen"])
        out1 = capsys.readouterr().out.strip()
        main(["keygen"])
        out2 = capsys.readouterr().out.strip()
        assert out1 != out2


class TestLockCLI:
    def test_lock_success(self, tmp_path, capsys):
        key = generate_key()
        env_file = tmp_path / ".env"
        vault_file = tmp_path / ".env.vault"
        env_file.write_text("FOO=bar\n", encoding="utf-8")

        rc = main([
            "lock",
            "--key", key,
            "--env", str(env_file),
            "--vault", str(vault_file),
        ])
        assert rc == 0
        assert vault_file.exists()
        captured = capsys.readouterr()
        assert "Locked" in captured.out

    def test_lock_missing_env_returns_error(self, tmp_path, capsys):
        rc = main([
            "lock",
            "--key", generate_key(),
            "--env", str(tmp_path / "missing.env"),
            "--vault", str(tmp_path / "out.vault"),
        ])
        assert rc == 1
        assert "Error" in capsys.readouterr().err


class TestUnlockCLI:
    def test_unlock_success(self, tmp_path, capsys):
        key = generate_key()
        env_file = tmp_path / ".env"
        vault_file = tmp_path / ".env.vault"
        env_file.write_text("FOO=bar\nBAZ=123\n", encoding="utf-8")

        main(["lock", "--key", key, "--env", str(env_file), "--vault", str(vault_file)])
        env_file.unlink()

        rc = main(["unlock", "--key", key, "--vault", str(vault_file), "--env", str(env_file)])
        assert rc == 0
        assert env_file.exists()
        captured = capsys.readouterr()
        assert "Unlocked" in captured.out
        assert "2 variables" in captured.out

    def test_unlock_wrong_key_returns_error(self, tmp_path, capsys):
        key = generate_key()
        env_file = tmp_path / ".env"
        vault_file = tmp_path / ".env.vault"
        env_file.write_text("FOO=bar\n", encoding="utf-8")

        main(["lock", "--key", key, "--env", str(env_file), "--vault", str(vault_file)])

        rc = main(["unlock", "--key", generate_key(), "--vault", str(vault_file), "--env", str(env_file)])
        assert rc == 1

    def test_unlock_missing_vault_returns_error(self, tmp_path, capsys):
        rc = main([
            "unlock",
            "--key", generate_key(),
            "--vault", str(tmp_path / "missing.vault"),
            "--env", str(tmp_path / ".env"),
        ])
        assert rc == 1
