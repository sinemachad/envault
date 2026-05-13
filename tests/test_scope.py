"""Tests for envault.scope."""

import pytest
from pathlib import Path

from envault.scope import add_scope, remove_scope, get_scope, list_scopes


@pytest.fixture()
def base_dir(tmp_path):
    return str(tmp_path)


class TestAddScope:
    def test_returns_dict_with_name_and_vault(self, base_dir):
        result = add_scope(base_dir, "dev", ".env.vault")
        assert result["name"] == "dev"
        assert result["vault"] == ".env.vault"

    def test_description_stored(self, base_dir):
        result = add_scope(base_dir, "staging", "staging.vault", description="Staging env")
        assert result["description"] == "Staging env"

    def test_scope_persisted_to_disk(self, base_dir):
        add_scope(base_dir, "prod", "prod.vault")
        found = get_scope(base_dir, "prod")
        assert found is not None
        assert found["vault"] == "prod.vault"

    def test_duplicate_name_raises(self, base_dir):
        add_scope(base_dir, "dev", ".env.vault")
        with pytest.raises(KeyError, match="dev"):
            add_scope(base_dir, "dev", "other.vault")

    def test_empty_name_raises(self, base_dir):
        with pytest.raises(ValueError):
            add_scope(base_dir, "", ".env.vault")

    def test_empty_vault_raises(self, base_dir):
        with pytest.raises(ValueError):
            add_scope(base_dir, "dev", "")

    def test_multiple_scopes_accumulate(self, base_dir):
        add_scope(base_dir, "dev", "dev.vault")
        add_scope(base_dir, "prod", "prod.vault")
        scopes = list_scopes(base_dir)
        names = [s["name"] for s in scopes]
        assert "dev" in names
        assert "prod" in names


class TestRemoveScope:
    def test_scope_removed(self, base_dir):
        add_scope(base_dir, "dev", "dev.vault")
        remove_scope(base_dir, "dev")
        assert get_scope(base_dir, "dev") is None

    def test_missing_scope_raises(self, base_dir):
        with pytest.raises(KeyError, match="nonexistent"):
            remove_scope(base_dir, "nonexistent")


class TestGetScope:
    def test_returns_none_for_missing(self, base_dir):
        assert get_scope(base_dir, "ghost") is None

    def test_returns_entry_for_existing(self, base_dir):
        add_scope(base_dir, "ci", "ci.vault", description="CI pipeline")
        result = get_scope(base_dir, "ci")
        assert result["vault"] == "ci.vault"
        assert result["description"] == "CI pipeline"


class TestListScopes:
    def test_empty_when_no_scopes(self, base_dir):
        assert list_scopes(base_dir) == []

    def test_returns_all_scopes(self, base_dir):
        add_scope(base_dir, "a", "a.vault")
        add_scope(base_dir, "b", "b.vault")
        result = list_scopes(base_dir)
        assert len(result) == 2
