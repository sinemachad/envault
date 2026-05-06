"""Tests for envault.access module."""

import json
import os
import pytest

from envault.access import (
    set_allowed_keys,
    get_allowed_keys,
    remove_policy,
    filter_env,
    list_policies,
    _get_policy_path,
)


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestSetAllowedKeys:
    def test_returns_profile_and_keys(self, base_dir):
        result = set_allowed_keys(base_dir, "dev", ["DB_URL", "SECRET"])
        assert result["profile"] == "dev"
        assert result["allowed_keys"] == ["DB_URL", "SECRET"]

    def test_persisted_to_disk(self, base_dir):
        set_allowed_keys(base_dir, "ci", ["CI_TOKEN"])
        path = _get_policy_path(base_dir)
        data = json.loads(path.read_text())
        assert "ci" in data
        assert data["ci"] == ["CI_TOKEN"]

    def test_overwrites_existing_policy(self, base_dir):
        set_allowed_keys(base_dir, "dev", ["OLD_KEY"])
        set_allowed_keys(base_dir, "dev", ["NEW_KEY"])
        assert get_allowed_keys(base_dir, "dev") == ["NEW_KEY"]

    def test_multiple_profiles_independent(self, base_dir):
        set_allowed_keys(base_dir, "dev", ["DEV_KEY"])
        set_allowed_keys(base_dir, "prod", ["PROD_KEY"])
        assert get_allowed_keys(base_dir, "dev") == ["DEV_KEY"]
        assert get_allowed_keys(base_dir, "prod") == ["PROD_KEY"]


class TestGetAllowedKeys:
    def test_returns_none_when_no_policy(self, base_dir):
        assert get_allowed_keys(base_dir, "nonexistent") is None

    def test_returns_keys_after_set(self, base_dir):
        set_allowed_keys(base_dir, "dev", ["A", "B"])
        assert get_allowed_keys(base_dir, "dev") == ["A", "B"]


class TestRemovePolicy:
    def test_returns_true_when_removed(self, base_dir):
        set_allowed_keys(base_dir, "dev", ["X"])
        assert remove_policy(base_dir, "dev") is True

    def test_returns_false_when_not_found(self, base_dir):
        assert remove_policy(base_dir, "ghost") is False

    def test_policy_no_longer_returned(self, base_dir):
        set_allowed_keys(base_dir, "dev", ["X"])
        remove_policy(base_dir, "dev")
        assert get_allowed_keys(base_dir, "dev") is None


class TestFilterEnv:
    def test_returns_all_when_none(self):
        env = {"A": "1", "B": "2"}
        assert filter_env(env, None) == env

    def test_filters_to_allowed_keys(self):
        env = {"A": "1", "B": "2", "C": "3"}
        assert filter_env(env, ["A", "C"]) == {"A": "1", "C": "3"}

    def test_missing_allowed_key_ignored(self):
        env = {"A": "1"}
        assert filter_env(env, ["A", "MISSING"]) == {"A": "1"}

    def test_empty_allowed_returns_empty(self):
        env = {"A": "1", "B": "2"}
        assert filter_env(env, []) == {}


class TestListPolicies:
    def test_returns_empty_when_no_file(self, base_dir):
        assert list_policies(base_dir) == {}

    def test_returns_all_profiles(self, base_dir):
        set_allowed_keys(base_dir, "dev", ["D"])
        set_allowed_keys(base_dir, "prod", ["P"])
        policies = list_policies(base_dir)
        assert "dev" in policies
        assert "prod" in policies
