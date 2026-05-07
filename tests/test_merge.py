"""Tests for envault.merge."""

import json
import os
import pytest

from envault.merge import (
    MergeConflict,
    MergeResult,
    has_conflicts,
    merge_envs,
    merge_vaults,
)
from envault.crypto import generate_key
from envault.vault import lock, unlock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def base():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "dev"}


@pytest.fixture()
def shared_key(tmp_path):
    return generate_key()


def _make_vault(path, env, key):
    lock(env, str(path), key)
    return str(path)


# ---------------------------------------------------------------------------
# has_conflicts
# ---------------------------------------------------------------------------


class TestHasConflicts:
    def test_no_conflicts(self):
        result = MergeResult(merged={"A": "1"})
        assert not has_conflicts(result)

    def test_with_conflicts(self):
        result = MergeResult(
            merged={"A": "1"},
            conflicts=[MergeConflict(key="A", ours="1", theirs="2")],
        )
        assert has_conflicts(result)


# ---------------------------------------------------------------------------
# merge_envs
# ---------------------------------------------------------------------------


class TestMergeEnvs:
    def test_no_changes_returns_base(self, base):
        result = merge_envs(base, base.copy(), base.copy())
        assert result.merged == base
        assert not has_conflicts(result)

    def test_detects_added_key(self, base):
        theirs = {**base, "NEW_KEY": "value"}
        result = merge_envs(base, base.copy(), theirs)
        assert "NEW_KEY" in result.merged
        assert "NEW_KEY" in result.added_keys

    def test_detects_removed_key(self, base):
        ours = {k: v for k, v in base.items() if k != "DB_PORT"}
        theirs = {k: v for k, v in base.items() if k != "DB_PORT"}
        result = merge_envs(base, ours, theirs)
        assert "DB_PORT" not in result.merged
        assert "DB_PORT" in result.removed_keys

    def test_ours_change_wins_when_theirs_unchanged(self, base):
        ours = {**base, "DB_HOST": "prod-server"}
        result = merge_envs(base, ours, base.copy())
        assert result.merged["DB_HOST"] == "prod-server"
        assert not has_conflicts(result)

    def test_theirs_change_wins_when_ours_unchanged(self, base):
        theirs = {**base, "APP_ENV": "production"}
        result = merge_envs(base, base.copy(), theirs)
        assert result.merged["APP_ENV"] == "production"
        assert not has_conflicts(result)

    def test_conflict_detected_on_dual_change(self, base):
        ours = {**base, "DB_HOST": "ours-host"}
        theirs = {**base, "DB_HOST": "theirs-host"}
        result = merge_envs(base, ours, theirs, strategy="ours")
        assert has_conflicts(result)
        assert result.conflicts[0].key == "DB_HOST"

    def test_strategy_ours_picks_our_value_on_conflict(self, base):
        ours = {**base, "DB_HOST": "ours-host"}
        theirs = {**base, "DB_HOST": "theirs-host"}
        result = merge_envs(base, ours, theirs, strategy="ours")
        assert result.merged["DB_HOST"] == "ours-host"

    def test_strategy_theirs_picks_their_value_on_conflict(self, base):
        ours = {**base, "DB_HOST": "ours-host"}
        theirs = {**base, "DB_HOST": "theirs-host"}
        result = merge_envs(base, ours, theirs, strategy="theirs")
        assert result.merged["DB_HOST"] == "theirs-host"

    def test_union_keeps_theirs_only_key(self, base):
        theirs = {**base, "ONLY_THEIRS": "yes"}
        ours_without = {k: v for k, v in base.items()}
        # Simulate ours deleting a key that theirs still has
        ours_without.pop("APP_ENV")
        result = merge_envs(base, ours_without, theirs, strategy="union")
        assert "APP_ENV" in result.merged


# ---------------------------------------------------------------------------
# merge_vaults
# ---------------------------------------------------------------------------


class TestMergeVaults:
    def test_produces_output_file(self, tmp_path, shared_key):
        base_env = {"KEY": "base"}
        ours_env = {"KEY": "ours"}
        theirs_env = {"KEY": "theirs", "EXTRA": "1"}
        base_p = _make_vault(tmp_path / "base.env.vault", base_env, shared_key)
        ours_p = _make_vault(tmp_path / "ours.env.vault", ours_env, shared_key)
        theirs_p = _make_vault(tmp_path / "theirs.env.vault", theirs_env, shared_key)
        out_p = str(tmp_path / "merged.env.vault")

        merge_vaults(base_p, ours_p, theirs_p, shared_key, out_p, strategy="ours")
        assert os.path.exists(out_p)

    def test_merged_vault_decryptable(self, tmp_path, shared_key):
        base_env = {"A": "1", "B": "2"}
        ours_env = {"A": "ours", "B": "2"}
        theirs_env = {"A": "1", "B": "theirs", "C": "new"}
        base_p = _make_vault(tmp_path / "base.vault", base_env, shared_key)
        ours_p = _make_vault(tmp_path / "ours.vault", ours_env, shared_key)
        theirs_p = _make_vault(tmp_path / "theirs.vault", theirs_env, shared_key)
        out_p = str(tmp_path / "out.vault")

        result = merge_vaults(base_p, ours_p, theirs_p, shared_key, out_p)
        decrypted = unlock(out_p, shared_key)
        assert decrypted["A"] == "ours"   # ours changed it
        assert decrypted["B"] == "theirs"  # theirs changed it
        assert decrypted["C"] == "new"    # theirs added it
