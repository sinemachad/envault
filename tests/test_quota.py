"""Tests for envault.quota."""

import json
import os
import pytest

from envault.quota import (
    DEFAULT_QUOTA,
    QuotaEntry,
    check_quota,
    get_quota,
    remove_quota,
    set_quota,
)


@pytest.fixture()
def base_dir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# QuotaEntry
# ---------------------------------------------------------------------------

class TestQuotaEntry:
    def test_remaining_is_limit_minus_current(self):
        entry = QuotaEntry(vault="dev", limit=50, current=20)
        assert entry.remaining == 30

    def test_remaining_never_negative(self):
        entry = QuotaEntry(vault="dev", limit=10, current=15)
        assert entry.remaining == 0

    def test_exceeded_when_over_limit(self):
        entry = QuotaEntry(vault="dev", limit=10, current=11)
        assert entry.exceeded is True

    def test_not_exceeded_at_limit(self):
        entry = QuotaEntry(vault="dev", limit=10, current=10)
        assert entry.exceeded is False

    def test_repr_contains_vault(self):
        entry = QuotaEntry(vault="prod", limit=100, current=5)
        assert "prod" in repr(entry)


# ---------------------------------------------------------------------------
# set_quota
# ---------------------------------------------------------------------------

class TestSetQuota:
    def test_returns_quota_entry(self, base_dir):
        result = set_quota(base_dir, "dev", 50)
        assert isinstance(result, QuotaEntry)

    def test_limit_stored_correctly(self, base_dir):
        set_quota(base_dir, "dev", 75)
        entry = get_quota(base_dir, "dev")
        assert entry.limit == 75

    def test_persisted_to_disk(self, base_dir):
        set_quota(base_dir, "staging", 30)
        quota_file = os.path.join(base_dir, ".envault", "quota.json")
        assert os.path.exists(quota_file)
        with open(quota_file) as f:
            data = json.load(f)
        assert data["staging"]["limit"] == 30

    def test_raises_on_zero_limit(self, base_dir):
        with pytest.raises(ValueError):
            set_quota(base_dir, "dev", 0)

    def test_raises_on_negative_limit(self, base_dir):
        with pytest.raises(ValueError):
            set_quota(base_dir, "dev", -5)


# ---------------------------------------------------------------------------
# get_quota
# ---------------------------------------------------------------------------

class TestGetQuota:
    def test_returns_default_when_not_set(self, base_dir):
        entry = get_quota(base_dir, "unknown")
        assert entry.limit == DEFAULT_QUOTA

    def test_returns_set_limit(self, base_dir):
        set_quota(base_dir, "prod", 200)
        entry = get_quota(base_dir, "prod")
        assert entry.limit == 200

    def test_vault_name_in_entry(self, base_dir):
        entry = get_quota(base_dir, "myapp")
        assert entry.vault == "myapp"


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

class TestCheckQuota:
    def test_allows_new_key_within_limit(self, base_dir):
        set_quota(base_dir, "dev", 5)
        keys = ["A", "B", "C"]
        entry = check_quota(base_dir, "dev", "D", keys)
        assert isinstance(entry, QuotaEntry)

    def test_raises_when_limit_exceeded(self, base_dir):
        set_quota(base_dir, "dev", 3)
        keys = ["A", "B", "C"]
        with pytest.raises(OverflowError, match="Quota exceeded"):
            check_quota(base_dir, "dev", "D", keys)

    def test_allows_update_of_existing_key(self, base_dir):
        set_quota(base_dir, "dev", 3)
        keys = ["A", "B", "C"]
        # "A" already exists — updating it should not raise
        entry = check_quota(base_dir, "dev", "A", keys)
        assert entry.current == 3


# ---------------------------------------------------------------------------
# remove_quota
# ---------------------------------------------------------------------------

class TestRemoveQuota:
    def test_returns_true_when_removed(self, base_dir):
        set_quota(base_dir, "dev", 50)
        assert remove_quota(base_dir, "dev") is True

    def test_returns_false_when_not_found(self, base_dir):
        assert remove_quota(base_dir, "ghost") is False

    def test_reverts_to_default_after_removal(self, base_dir):
        set_quota(base_dir, "dev", 10)
        remove_quota(base_dir, "dev")
        entry = get_quota(base_dir, "dev")
        assert entry.limit == DEFAULT_QUOTA
