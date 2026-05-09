"""Tests for envault.rollback."""

from __future__ import annotations

import json
import os
import pytest

from envault.crypto import generate_key
from envault.vault import lock, unlock
from envault.history import record_change
from envault.rollback import list_rollback_points, rollback, RollbackResult


@pytest.fixture()
def shared_key():
    return generate_key()


@pytest.fixture()
def vault_file(tmp_path, shared_key):
    path = str(tmp_path / "test.vault")
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    lock(env, path, shared_key)
    return path


def _add_snapshot(vault_path, key, action="test-action"):
    env = unlock(vault_path, key)
    record_change(vault_path, action=action, snapshot=env)


class TestListRollbackPoints:
    def test_empty_when_no_history(self, vault_file):
        points = list_rollback_points(vault_file)
        assert points == []

    def test_returns_entries_with_snapshots(self, vault_file, shared_key):
        _add_snapshot(vault_file, shared_key, action="lock")
        points = list_rollback_points(vault_file)
        assert len(points) == 1
        assert points[0]["action"] == "lock"

    def test_excludes_entries_without_snapshots(self, vault_file, shared_key):
        record_change(vault_file, action="no-snap")
        _add_snapshot(vault_file, shared_key, action="with-snap")
        points = list_rollback_points(vault_file)
        assert all("snapshot" in p for p in points)
        assert len(points) == 1


class TestRollback:
    def test_returns_rollback_result(self, vault_file, shared_key):
        _add_snapshot(vault_file, shared_key, action="initial")
        result = rollback(vault_file, shared_key, index=0)
        assert isinstance(result, RollbackResult)

    def test_rolled_back_to_matches_action(self, vault_file, shared_key):
        _add_snapshot(vault_file, shared_key, action="my-snapshot")
        result = rollback(vault_file, shared_key, index=0)
        assert result.rolled_back_to == "my-snapshot"

    def test_vault_decryptable_after_rollback(self, vault_file, shared_key):
        _add_snapshot(vault_file, shared_key, action="snap")
        rollback(vault_file, shared_key, index=0)
        env = unlock(vault_file, shared_key)
        assert "DB_HOST" in env

    def test_keys_restored_count(self, vault_file, shared_key):
        _add_snapshot(vault_file, shared_key, action="snap")
        result = rollback(vault_file, shared_key, index=0)
        assert result.keys_restored == 2

    def test_raises_when_no_rollback_points(self, vault_file, shared_key):
        with pytest.raises(ValueError, match="No rollback points"):
            rollback(vault_file, shared_key)

    def test_raises_on_out_of_range_index(self, vault_file, shared_key):
        _add_snapshot(vault_file, shared_key)
        with pytest.raises(IndexError):
            rollback(vault_file, shared_key, index=99)
