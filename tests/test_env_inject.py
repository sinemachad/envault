"""Tests for envault.env_inject."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from envault.crypto import generate_key
from envault.vault import lock
from envault.env_inject import inject_env, InjectionResult


@pytest.fixture()
def vault_file(tmp_path: Path):
    key = generate_key()
    env_path = tmp_path / ".env"
    vault_path = tmp_path / ".env.vault"
    env_path.write_text("APP_NAME=envault\nDEBUG=true\nSECRET=s3cr3t\n")
    lock(str(env_path), str(vault_path), key)
    return str(vault_path), key


class TestInjectEnv:
    def test_returns_injection_result(self, vault_file, monkeypatch):
        monkeypatch.delenv("APP_NAME", raising=False)
        path, key = vault_file
        result = inject_env(path, key)
        assert isinstance(result, InjectionResult)

    def test_variables_present_in_os_environ(self, vault_file, monkeypatch):
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("SECRET", raising=False)
        path, key = vault_file
        inject_env(path, key)
        assert os.environ["APP_NAME"] == "envault"
        assert os.environ["DEBUG"] == "true"

    def test_injected_list_contains_all_keys(self, vault_file, monkeypatch):
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("SECRET", raising=False)
        path, key = vault_file
        result = inject_env(path, key)
        assert set(result.injected) == {"APP_NAME", "DEBUG", "SECRET"}
        assert result.skipped == []

    def test_existing_var_not_overwritten_by_default(self, vault_file, monkeypatch):
        monkeypatch.setenv("APP_NAME", "original")
        path, key = vault_file
        result = inject_env(path, key)
        assert os.environ["APP_NAME"] == "original"
        assert "APP_NAME" in result.skipped

    def test_overwrite_flag_replaces_existing_var(self, vault_file, monkeypatch):
        monkeypatch.setenv("APP_NAME", "original")
        path, key = vault_file
        result = inject_env(path, key, overwrite=True)
        assert os.environ["APP_NAME"] == "envault"
        assert "APP_NAME" in result.injected
        assert "APP_NAME" not in result.skipped

    def test_wrong_key_raises(self, vault_file, monkeypatch):
        path, _ = vault_file
        bad_key = generate_key()
        with pytest.raises(Exception):
            inject_env(path, bad_key)

    def test_missing_vault_raises(self, tmp_path):
        with pytest.raises(Exception):
            inject_env(str(tmp_path / "nonexistent.vault"), generate_key())
