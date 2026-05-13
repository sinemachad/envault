"""Tests for envault.aliases."""

import os
import pytest
from envault.aliases import add_alias, remove_alias, resolve_alias, list_aliases


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestAddAlias:
    def test_returns_dict_with_alias_and_target(self, base_dir):
        result = add_alias("db", "DATABASE_URL", base_dir)
        assert result["alias"] == "db"
        assert result["target"] == "DATABASE_URL"

    def test_alias_persisted_to_disk(self, base_dir):
        add_alias("db", "DATABASE_URL", base_dir)
        assert os.path.exists(os.path.join(base_dir, "aliases.json"))

    def test_multiple_aliases_accumulate(self, base_dir):
        add_alias("db", "DATABASE_URL", base_dir)
        add_alias("redis", "REDIS_URL", base_dir)
        aliases = list_aliases(base_dir)
        keys = [a["alias"] for a in aliases]
        assert "db" in keys
        assert "redis" in keys

    def test_overwrite_existing_alias(self, base_dir):
        add_alias("db", "DATABASE_URL", base_dir)
        add_alias("db", "POSTGRES_URL", base_dir)
        assert resolve_alias("db", base_dir) == "POSTGRES_URL"

    def test_empty_alias_raises(self, base_dir):
        with pytest.raises(ValueError):
            add_alias("", "DATABASE_URL", base_dir)

    def test_empty_target_raises(self, base_dir):
        with pytest.raises(ValueError):
            add_alias("db", "", base_dir)


class TestRemoveAlias:
    def test_removes_existing_alias(self, base_dir):
        add_alias("db", "DATABASE_URL", base_dir)
        remove_alias("db", base_dir)
        assert resolve_alias("db", base_dir) is None

    def test_missing_alias_raises(self, base_dir):
        with pytest.raises(KeyError):
            remove_alias("nonexistent", base_dir)


class TestResolveAlias:
    def test_returns_target_for_known_alias(self, base_dir):
        add_alias("secret", "SECRET_KEY", base_dir)
        assert resolve_alias("secret", base_dir) == "SECRET_KEY"

    def test_returns_none_for_unknown_alias(self, base_dir):
        assert resolve_alias("ghost", base_dir) is None


class TestListAliases:
    def test_empty_when_no_aliases(self, base_dir):
        assert list_aliases(base_dir) == []

    def test_returns_sorted_list(self, base_dir):
        add_alias("z_alias", "Z_VAR", base_dir)
        add_alias("a_alias", "A_VAR", base_dir)
        names = [a["alias"] for a in list_aliases(base_dir)]
        assert names == sorted(names)
