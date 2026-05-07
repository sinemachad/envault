"""Tests for envault.compare."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from envault.crypto import generate_key
from envault.vault import lock
from envault.compare import compare_vaults, format_compare, CompareResult


@pytest.fixture()
def shared_key():
    return generate_key()


def _make_vault(tmp_path: Path, env: dict, key: str, name: str = "vault.env.enc") -> str:
    path = tmp_path / name
    env_text = "\n".join(f"{k}={v}" for k, v in env.items())
    path.write_text(lock(env_text, key))
    return str(path)


class TestCompareVaults:
    def test_returns_compare_result(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"A": "1"}, shared_key, "left.enc")
        right = _make_vault(tmp_path, {"A": "1"}, shared_key, "right.enc")
        result = compare_vaults(left, right, key=shared_key)
        assert isinstance(result, CompareResult)

    def test_identical_vaults_no_differences(self, tmp_path, shared_key):
        env = {"FOO": "bar", "BAZ": "qux"}
        left = _make_vault(tmp_path, env, shared_key, "left.enc")
        right = _make_vault(tmp_path, env, shared_key, "right.enc")
        result = compare_vaults(left, right, key=shared_key)
        assert not result.has_differences()
        assert sorted(result.unchanged) == ["BAZ", "FOO"]

    def test_detects_only_in_left(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"A": "1", "B": "2"}, shared_key, "left.enc")
        right = _make_vault(tmp_path, {"A": "1"}, shared_key, "right.enc")
        result = compare_vaults(left, right, key=shared_key)
        assert "B" in result.only_in_left
        assert result.has_differences()

    def test_detects_only_in_right(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"A": "1"}, shared_key, "left.enc")
        right = _make_vault(tmp_path, {"A": "1", "C": "3"}, shared_key, "right.enc")
        result = compare_vaults(left, right, key=shared_key)
        assert "C" in result.only_in_right

    def test_detects_changed_keys(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"X": "old"}, shared_key, "left.enc")
        right = _make_vault(tmp_path, {"X": "new"}, shared_key, "right.enc")
        result = compare_vaults(left, right, key=shared_key)
        assert "X" in result.changed

    def test_masks_values_by_default(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"SECRET": "alpha"}, shared_key, "left.enc")
        right = _make_vault(tmp_path, {"SECRET": "beta"}, shared_key, "right.enc")
        result = compare_vaults(left, right, key=shared_key, mask_values=True)
        lv, rv = result.changed["SECRET"]
        assert lv == "***" and rv == "***"

    def test_show_values_when_requested(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"SECRET": "alpha"}, shared_key, "left.enc")
        right = _make_vault(tmp_path, {"SECRET": "beta"}, shared_key, "right.enc")
        result = compare_vaults(left, right, key=shared_key, mask_values=False)
        lv, rv = result.changed["SECRET"]
        assert lv == "alpha" and rv == "beta"

    def test_different_keys_per_vault(self, tmp_path):
        key_l = generate_key()
        key_r = generate_key()
        left = _make_vault(tmp_path, {"A": "1"}, key_l, "left.enc")
        right = _make_vault(tmp_path, {"A": "1"}, key_r, "right.enc")
        result = compare_vaults(left, right, key=key_l, left_key=key_l, right_key=key_r)
        assert not result.has_differences()


class TestFormatCompare:
    def test_no_diff_message(self, tmp_path, shared_key):
        env = {"K": "v"}
        left = _make_vault(tmp_path, env, shared_key, "l.enc")
        right = _make_vault(tmp_path, env, shared_key, "r.enc")
        result = compare_vaults(left, right, key=shared_key)
        output = format_compare(result)
        assert "No differences found" in output

    def test_summary_line_present(self, tmp_path, shared_key):
        left = _make_vault(tmp_path, {"A": "1", "B": "2"}, shared_key, "l.enc")
        right = _make_vault(tmp_path, {"A": "9", "C": "3"}, shared_key, "r.enc")
        result = compare_vaults(left, right, key=shared_key)
        output = format_compare(result)
        assert "only-left" in output
        assert "changed" in output
