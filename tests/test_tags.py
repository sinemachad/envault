"""Tests for envault.tags module."""
import json
import pytest
from pathlib import Path
from envault.tags import add_tag, remove_tag, list_tags, find_by_tag


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


class TestAddTag:
    def test_returns_dict_with_vault_and_tags(self, base_dir):
        result = add_tag("secrets.vault", "production", base_dir)
        assert result["vault_file"] == "secrets.vault"
        assert "production" in result["tags"]

    def test_tag_persisted_to_disk(self, base_dir):
        add_tag("secrets.vault", "staging", base_dir)
        tags_file = Path(base_dir) / ".envault_tags.json"
        assert tags_file.exists()
        data = json.loads(tags_file.read_text())
        assert "staging" in data["secrets.vault"]

    def test_multiple_tags_accumulate(self, base_dir):
        add_tag("secrets.vault", "production", base_dir)
        result = add_tag("secrets.vault", "backend", base_dir)
        assert "production" in result["tags"]
        assert "backend" in result["tags"]

    def test_duplicate_tag_not_added_twice(self, base_dir):
        add_tag("secrets.vault", "production", base_dir)
        result = add_tag("secrets.vault", "production", base_dir)
        assert result["tags"].count("production") == 1

    def test_different_vault_files_independent(self, base_dir):
        add_tag("a.vault", "alpha", base_dir)
        add_tag("b.vault", "beta", base_dir)
        assert list_tags("a.vault", base_dir) == ["alpha"]
        assert list_tags("b.vault", base_dir) == ["beta"]


class TestRemoveTag:
    def test_removes_existing_tag(self, base_dir):
        add_tag("secrets.vault", "production", base_dir)
        result = remove_tag("secrets.vault", "production", base_dir)
        assert "production" not in result["tags"]

    def test_raises_if_tag_not_present(self, base_dir):
        with pytest.raises(ValueError, match="Tag 'missing' not found"):
            remove_tag("secrets.vault", "missing", base_dir)

    def test_other_tags_unaffected(self, base_dir):
        add_tag("secrets.vault", "production", base_dir)
        add_tag("secrets.vault", "backend", base_dir)
        remove_tag("secrets.vault", "production", base_dir)
        assert list_tags("secrets.vault", base_dir) == ["backend"]


class TestListTags:
    def test_returns_empty_list_for_unknown_file(self, base_dir):
        result = list_tags("unknown.vault", base_dir)
        assert result == []

    def test_returns_all_tags(self, base_dir):
        add_tag("secrets.vault", "x", base_dir)
        add_tag("secrets.vault", "y", base_dir)
        assert set(list_tags("secrets.vault", base_dir)) == {"x", "y"}


class TestFindByTag:
    def test_finds_vault_files_with_tag(self, base_dir):
        add_tag("a.vault", "production", base_dir)
        add_tag("b.vault", "production", base_dir)
        add_tag("c.vault", "staging", base_dir)
        result = find_by_tag("production", base_dir)
        assert "a.vault" in result
        assert "b.vault" in result
        assert "c.vault" not in result

    def test_returns_empty_list_for_unknown_tag(self, base_dir):
        assert find_by_tag("nonexistent", base_dir) == []
