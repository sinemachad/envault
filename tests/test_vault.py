"""Tests for envault.vault module."""

import json
import pytest
from pathlib import Path

from envault.vault import parse_env, serialize_env, lock, unlock
from envault.crypto import generate_key


SAMPLE_ENV = """# Sample env file
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
SECRET_KEY=super_secret_value
DEBUG=true
"""


class TestParseEnv:
    def test_parses_simple_key_value(self):
        result = parse_env("FOO=bar\nBAZ=qux")
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_comments(self):
        result = parse_env("# comment\nFOO=bar")
        assert "FOO" in result
        assert len(result) == 1

    def test_ignores_blank_lines(self):
        result = parse_env("\n\nFOO=bar\n\n")
        assert result == {"FOO": "bar"}

    def test_strips_quoted_values(self):
        result = parse_env('FOO="hello world"')
        assert result["FOO"] == "hello world"

    def test_handles_empty_string(self):
        assert parse_env("") == {}

    def test_skips_lines_without_equals(self):
        result = parse_env("INVALID_LINE\nFOO=bar")
        assert result == {"FOO": "bar"}


class TestSerializeEnv:
    def test_produces_key_value_lines(self):
        result = serialize_env({"FOO": "bar"})
        assert "FOO=bar" in result

    def test_quotes_values_with_spaces(self):
        result = serialize_env({"FOO": "hello world"})
        assert 'FOO="hello world"' in result

    def test_ends_with_newline(self):
        result = serialize_env({"A": "1"})
        assert result.endswith("\n")


class TestLockUnlock:
    def test_roundtrip(self, tmp_path):
        key = generate_key()
        env_file = tmp_path / ".env"
        vault_file = tmp_path / ".env.vault"
        env_file.write_text(SAMPLE_ENV, encoding="utf-8")

        lock(key, env_path=str(env_file), vault_path=str(vault_file))
        assert vault_file.exists()

        result = unlock(key, vault_path=str(vault_file), env_path=str(env_file))
        assert result["DB_HOST"] == "localhost"
        assert result["SECRET_KEY"] == "super_secret_value"

    def test_vault_file_is_valid_json(self, tmp_path):
        key = generate_key()
        env_file = tmp_path / ".env"
        vault_file = tmp_path / ".env.vault"
        env_file.write_text("FOO=bar", encoding="utf-8")

        lock(key, env_path=str(env_file), vault_path=str(vault_file))
        data = json.loads(vault_file.read_text())
        assert "token" in data
        assert data["version"] == 1

    def test_lock_raises_if_env_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            lock(generate_key(), env_path=str(tmp_path / "nonexistent.env"))

    def test_unlock_raises_if_vault_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            unlock(generate_key(), vault_path=str(tmp_path / "nonexistent.vault"))

    def test_wrong_key_raises(self, tmp_path):
        key = generate_key()
        wrong_key = generate_key()
        env_file = tmp_path / ".env"
        vault_file = tmp_path / ".env.vault"
        env_file.write_text("FOO=bar", encoding="utf-8")

        lock(key, env_path=str(env_file), vault_path=str(vault_file))
        with pytest.raises(Exception):
            unlock(wrong_key, vault_path=str(vault_file), env_path=str(env_file))
