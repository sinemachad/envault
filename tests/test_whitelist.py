"""Tests for envault.whitelist."""

import os
import pytest

from envault.whitelist import (
    set_whitelist,
    get_whitelist,
    remove_whitelist,
    check_keys,
)


@pytest.fixture()
def base_dir(tmp_path):
    return str(tmp_path)


class TestSetWhitelist:
    def test_returns_dict_with_vault_and_keys(self, base_dir):
        result = set_whitelist(base_dir, "prod", ["DB_URL", "SECRET_KEY"])
        assert result["vault"] == "prod"
        assert "DB_URL" in result["allowed_keys"]

    def test_keys_are_sorted_and_deduplicated(self, base_dir):
        result = set_whitelist(base_dir, "prod", ["Z_KEY", "A_KEY", "A_KEY"])
        assert result["allowed_keys"] == ["A_KEY", "Z_KEY"]

    def test_persisted_to_disk(self, base_dir):
        set_whitelist(base_dir, "prod", ["DB_URL"])
        assert get_whitelist(base_dir, "prod") == ["DB_URL"]

    def test_overwrites_existing_whitelist(self, base_dir):
        set_whitelist(base_dir, "prod", ["OLD_KEY"])
        set_whitelist(base_dir, "prod", ["NEW_KEY"])
        assert get_whitelist(base_dir, "prod") == ["NEW_KEY"]

    def test_empty_keys_raises(self, base_dir):
        with pytest.raises(ValueError):
            set_whitelist(base_dir, "prod", [])

    def test_multiple_vaults_independent(self, base_dir):
        set_whitelist(base_dir, "prod", ["PROD_KEY"])
        set_whitelist(base_dir, "staging", ["STAGING_KEY"])
        assert get_whitelist(base_dir, "prod") == ["PROD_KEY"]
        assert get_whitelist(base_dir, "staging") == ["STAGING_KEY"]


class TestGetWhitelist:
    def test_returns_none_when_no_whitelist(self, base_dir):
        assert get_whitelist(base_dir, "missing") is None

    def test_returns_list_after_set(self, base_dir):
        set_whitelist(base_dir, "dev", ["FOO", "BAR"])
        result = get_whitelist(base_dir, "dev")
        assert isinstance(result, list)
        assert "FOO" in result


class TestRemoveWhitelist:
    def test_returns_true_when_removed(self, base_dir):
        set_whitelist(base_dir, "prod", ["KEY"])
        assert remove_whitelist(base_dir, "prod") is True

    def test_returns_false_when_not_found(self, base_dir):
        assert remove_whitelist(base_dir, "ghost") is False

    def test_whitelist_gone_after_remove(self, base_dir):
        set_whitelist(base_dir, "prod", ["KEY"])
        remove_whitelist(base_dir, "prod")
        assert get_whitelist(base_dir, "prod") is None


class TestCheckKeys:
    def test_all_allowed_when_no_whitelist(self, base_dir):
        result = check_keys(base_dir, "prod", ["ANY_KEY"])
        assert result["denied"] == []
        assert result["whitelisted"] is None

    def test_allowed_keys_pass(self, base_dir):
        set_whitelist(base_dir, "prod", ["DB_URL", "PORT"])
        result = check_keys(base_dir, "prod", ["DB_URL", "PORT"])
        assert result["denied"] == []
        assert set(result["allowed"]) == {"DB_URL", "PORT"}

    def test_denied_keys_flagged(self, base_dir):
        set_whitelist(base_dir, "prod", ["DB_URL"])
        result = check_keys(base_dir, "prod", ["DB_URL", "SECRET"])
        assert "SECRET" in result["denied"]
        assert "DB_URL" in result["allowed"]
