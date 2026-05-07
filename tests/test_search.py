"""Tests for envault.search module."""

import os
import pytest

from envault.crypto import generate_key
from envault.vault import lock
from envault.search import (
    FileSearchResult,
    SearchResult,
    format_search_results,
    search_multiple_vaults,
    search_vault,
)


ENV_CONTENT = """DB_HOST=localhost
DB_PORT=5432
API_KEY=supersecret
DEBUG=false
"""


@pytest.fixture
def vault_file(tmp_path):
    key = generate_key()
    path = str(tmp_path / "test.vault")
    lock(ENV_CONTENT, path, key)
    return path, key


class TestSearchVault:
    def test_returns_file_search_result(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key)
        assert isinstance(result, FileSearchResult)

    def test_returns_all_keys_without_pattern(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key)
        assert len(result.matches) == 4

    def test_pattern_filters_keys(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key, pattern="^DB_")
        keys = [m.key for m in result.matches]
        assert "DB_HOST" in keys
        assert "DB_PORT" in keys
        assert "API_KEY" not in keys

    def test_pattern_is_case_insensitive(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key, pattern="db_")
        assert len(result.matches) == 2

    def test_values_masked_by_default(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key)
        for match in result.matches:
            assert match.value == "***"
            assert match.masked is True

    def test_values_revealed_when_requested(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key, mask_values=False)
        values = {m.key: m.value for m in result.matches}
        assert values["DB_HOST"] == "localhost"
        assert values["API_KEY"] == "supersecret"

    def test_no_matches_returns_empty_list(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key, pattern="NONEXISTENT_KEY")
        assert result.matches == []
        assert result.has_matches() is False

    def test_has_matches_true_when_results_exist(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key, pattern="API")
        assert result.has_matches() is True


class TestSearchMultipleVaults:
    def test_returns_list_of_file_results(self, vault_file, tmp_path):
        path, key = vault_file
        path2 = str(tmp_path / "second.vault")
        lock("FOO=bar\n", path2, key)
        results = search_multiple_vaults([path, path2], key)
        assert len(results) == 2

    def test_error_vault_captured_gracefully(self, vault_file):
        path, key = vault_file
        results = search_multiple_vaults([path, "/nonexistent/file.vault"], key)
        assert len(results) == 2
        error_result = results[1]
        assert error_result.matches[0].key == "__error__"


class TestFormatSearchResults:
    def test_returns_string(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key, pattern="DB_HOST")
        output = format_search_results([result])
        assert isinstance(output, str)

    def test_includes_vault_path(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key, pattern="DB_HOST")
        output = format_search_results([result])
        assert path in output

    def test_no_matches_shows_message(self, vault_file):
        path, key = vault_file
        result = search_vault(path, key, pattern="ZZZNOPE")
        output = format_search_results([result])
        assert "no matches" in output
