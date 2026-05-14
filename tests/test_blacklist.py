"""Tests for envault.blacklist."""

import pytest
from envault.blacklist import (
    set_blacklist,
    get_blacklist,
    remove_blacklist,
    check_blacklist,
)


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestSetBlacklist:
    def test_returns_dict_with_vault_and_keys(self, base_dir):
        result = set_blacklist(base_dir, "prod", ["SECRET", "TOKEN"])
        assert result["vault"] == "prod"
        assert "SECRET" in result["keys"]
        assert "TOKEN" in result["keys"]

    def test_keys_are_sorted_and_deduplicated(self, base_dir):
        result = set_blacklist(base_dir, "prod", ["Z_KEY", "A_KEY", "A_KEY"])
        assert result["keys"] == ["A_KEY", "Z_KEY"]

    def test_persisted_to_disk(self, base_dir):
        set_blacklist(base_dir, "prod", ["SECRET"])
        loaded = get_blacklist(base_dir, "prod")
        assert "SECRET" in loaded

    def test_raises_on_empty_keys(self, base_dir):
        with pytest.raises(ValueError):
            set_blacklist(base_dir, "prod", [])

    def test_overwrites_existing_entry(self, base_dir):
        set_blacklist(base_dir, "prod", ["OLD_KEY"])
        set_blacklist(base_dir, "prod", ["NEW_KEY"])
        keys = get_blacklist(base_dir, "prod")
        assert keys == ["NEW_KEY"]

    def test_multiple_vaults_independent(self, base_dir):
        set_blacklist(base_dir, "prod", ["PROD_SECRET"])
        set_blacklist(base_dir, "dev", ["DEV_SECRET"])
        assert get_blacklist(base_dir, "prod") == ["PROD_SECRET"]
        assert get_blacklist(base_dir, "dev") == ["DEV_SECRET"]


class TestGetBlacklist:
    def test_returns_empty_list_when_no_entry(self, base_dir):
        result = get_blacklist(base_dir, "missing")
        assert result == []

    def test_returns_keys_after_set(self, base_dir):
        set_blacklist(base_dir, "staging", ["API_KEY"])
        result = get_blacklist(base_dir, "staging")
        assert "API_KEY" in result


class TestRemoveBlacklist:
    def test_returns_true_when_removed(self, base_dir):
        set_blacklist(base_dir, "prod", ["SECRET"])
        assert remove_blacklist(base_dir, "prod") is True

    def test_returns_false_when_not_found(self, base_dir):
        assert remove_blacklist(base_dir, "ghost") is False

    def test_entry_no_longer_accessible_after_removal(self, base_dir):
        set_blacklist(base_dir, "prod", ["SECRET"])
        remove_blacklist(base_dir, "prod")
        assert get_blacklist(base_dir, "prod") == []


class TestCheckBlacklist:
    def test_returns_empty_when_no_blacklist(self, base_dir):
        result = check_blacklist(base_dir, "prod", ["KEY1", "KEY2"])
        assert result == []

    def test_returns_matching_blacklisted_keys(self, base_dir):
        set_blacklist(base_dir, "prod", ["SECRET", "TOKEN"])
        result = check_blacklist(base_dir, "prod", ["SECRET", "SAFE_KEY"])
        assert result == ["SECRET"]

    def test_returns_all_violations_when_multiple_match(self, base_dir):
        set_blacklist(base_dir, "prod", ["A", "B", "C"])
        result = check_blacklist(base_dir, "prod", ["A", "B", "D"])
        assert set(result) == {"A", "B"}

    def test_no_false_positives(self, base_dir):
        set_blacklist(base_dir, "prod", ["FORBIDDEN"])
        result = check_blacklist(base_dir, "prod", ["ALLOWED", "ALSO_ALLOWED"])
        assert result == []
