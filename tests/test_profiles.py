"""Tests for envault.profiles module."""

import json
import pytest
from pathlib import Path
from envault.profiles import (
    add_profile,
    remove_profile,
    get_profile,
    list_profiles,
    _get_profiles_path,
)


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestAddProfile:
    def test_returns_profile_dict(self, base_dir):
        result = add_profile("staging", ".env.staging.vault", base_dir)
        assert result["vault_file"] == ".env.staging.vault"

    def test_profile_persisted_to_disk(self, base_dir):
        add_profile("prod", ".env.prod.vault", base_dir)
        path = _get_profiles_path(base_dir)
        assert path.exists()
        with open(path) as f:
            data = json.load(f)
        assert "prod" in data

    def test_duplicate_name_raises(self, base_dir):
        add_profile("dev", ".env.dev.vault", base_dir)
        with pytest.raises(ValueError, match="already exists"):
            add_profile("dev", ".env.dev2.vault", base_dir)

    def test_multiple_profiles_stored(self, base_dir):
        add_profile("dev", ".env.dev.vault", base_dir)
        add_profile("staging", ".env.staging.vault", base_dir)
        profiles = list_profiles(base_dir)
        assert "dev" in profiles
        assert "staging" in profiles


class TestGetProfile:
    def test_returns_correct_vault_file(self, base_dir):
        add_profile("qa", ".env.qa.vault", base_dir)
        profile = get_profile("qa", base_dir)
        assert profile["vault_file"] == ".env.qa.vault"

    def test_missing_profile_raises(self, base_dir):
        with pytest.raises(KeyError, match="not found"):
            get_profile("nonexistent", base_dir)


class TestRemoveProfile:
    def test_removes_profile(self, base_dir):
        add_profile("temp", ".env.temp.vault", base_dir)
        remove_profile("temp", base_dir)
        assert "temp" not in list_profiles(base_dir)

    def test_remove_nonexistent_raises(self, base_dir):
        with pytest.raises(KeyError, match="not found"):
            remove_profile("ghost", base_dir)


class TestListProfiles:
    def test_empty_when_no_profiles(self, base_dir):
        assert list_profiles(base_dir) == []

    def test_returns_all_names(self, base_dir):
        add_profile("a", "a.vault", base_dir)
        add_profile("b", "b.vault", base_dir)
        names = list_profiles(base_dir)
        assert set(names) == {"a", "b"}
