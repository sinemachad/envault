"""Tests for envault.dependencies."""

import os
import pytest

from envault.dependencies import (
    add_dependency,
    remove_dependency,
    get_dependencies,
    list_all_dependencies,
    check_missing,
)


@pytest.fixture()
def base_dir(tmp_path):
    d = tmp_path / "deps"
    d.mkdir()
    return str(d)


@pytest.fixture()
def vault_file(tmp_path):
    v = tmp_path / "secrets.vault"
    v.write_text("")
    return str(v)


class TestAddDependency:
    def test_returns_dict_with_key_and_depends_on(self, vault_file, base_dir):
        result = add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        assert result["key"] == "DB_URL"
        assert "DB_HOST" in result["depends_on"]

    def test_dependency_persisted_to_disk(self, vault_file, base_dir):
        add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        deps = get_dependencies(vault_file, "DB_URL", base_dir)
        assert "DB_HOST" in deps

    def test_multiple_deps_accumulate(self, vault_file, base_dir):
        add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        add_dependency(vault_file, "DB_URL", "DB_PORT", base_dir)
        deps = get_dependencies(vault_file, "DB_URL", base_dir)
        assert "DB_HOST" in deps
        assert "DB_PORT" in deps

    def test_duplicate_dep_not_added_twice(self, vault_file, base_dir):
        add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        deps = get_dependencies(vault_file, "DB_URL", base_dir)
        assert deps.count("DB_HOST") == 1

    def test_self_dependency_raises(self, vault_file, base_dir):
        with pytest.raises(ValueError):
            add_dependency(vault_file, "KEY", "KEY", base_dir)


class TestRemoveDependency:
    def test_removes_existing_dep(self, vault_file, base_dir):
        add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        remove_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        deps = get_dependencies(vault_file, "DB_URL", base_dir)
        assert "DB_HOST" not in deps

    def test_raises_when_dep_not_found(self, vault_file, base_dir):
        with pytest.raises(KeyError):
            remove_dependency(vault_file, "DB_URL", "NONEXISTENT", base_dir)

    def test_key_removed_when_no_deps_remain(self, vault_file, base_dir):
        add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        remove_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        all_deps = list_all_dependencies(vault_file, base_dir)
        assert "DB_URL" not in all_deps


class TestCheckMissing:
    def test_no_missing_when_all_present(self, vault_file, base_dir):
        add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        env = {"DB_URL": "postgres://...", "DB_HOST": "localhost"}
        result = check_missing(vault_file, env, base_dir)
        assert result == {}

    def test_flags_absent_dependency(self, vault_file, base_dir):
        add_dependency(vault_file, "DB_URL", "DB_HOST", base_dir)
        env = {"DB_URL": "postgres://..."}
        result = check_missing(vault_file, env, base_dir)
        assert "DB_URL" in result
        assert "DB_HOST" in result["DB_URL"]

    def test_empty_env_flags_all(self, vault_file, base_dir):
        add_dependency(vault_file, "A", "B", base_dir)
        add_dependency(vault_file, "A", "C", base_dir)
        result = check_missing(vault_file, {}, base_dir)
        assert set(result["A"]) == {"B", "C"}
