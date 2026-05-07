"""Tests for envault.export."""

import json
import pytest

from envault.export import (
    export_env,
    ExportResult,
    FORMAT_DOTENV,
    FORMAT_JSON,
    FORMAT_SHELL,
    FORMAT_CSV,
    SUPPORTED_FORMATS,
)

SAMPLE = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "s3cr3t"}


class TestExportEnvDotenv:
    def test_returns_export_result(self):
        r = export_env(SAMPLE, FORMAT_DOTENV)
        assert isinstance(r, ExportResult)

    def test_format_attribute(self):
        r = export_env(SAMPLE, FORMAT_DOTENV)
        assert r.format == FORMAT_DOTENV

    def test_count_matches_env(self):
        r = export_env(SAMPLE, FORMAT_DOTENV)
        assert r.count == len(SAMPLE)

    def test_content_has_key_equals_value(self):
        r = export_env(SAMPLE, FORMAT_DOTENV)
        assert "DB_HOST=localhost" in r.content

    def test_keys_list_populated(self):
        r = export_env(SAMPLE, FORMAT_DOTENV)
        assert set(r.keys) == set(SAMPLE.keys())


class TestExportEnvJson:
    def test_content_is_valid_json(self):
        r = export_env(SAMPLE, FORMAT_JSON)
        parsed = json.loads(r.content)
        assert parsed["DB_HOST"] == "localhost"

    def test_all_keys_present(self):
        r = export_env(SAMPLE, FORMAT_JSON)
        parsed = json.loads(r.content)
        assert set(parsed.keys()) == set(SAMPLE.keys())


class TestExportEnvShell:
    def test_content_has_export_prefix(self):
        r = export_env(SAMPLE, FORMAT_SHELL)
        assert "export DB_HOST=localhost" in r.content

    def test_every_line_starts_with_export(self):
        r = export_env(SAMPLE, FORMAT_SHELL)
        for line in r.content.splitlines():
            assert line.startswith("export ")


class TestExportEnvCsv:
    def test_first_line_is_header(self):
        r = export_env(SAMPLE, FORMAT_CSV)
        assert r.content.splitlines()[0] == "key,value"

    def test_row_count(self):
        r = export_env(SAMPLE, FORMAT_CSV)
        # header + one row per key
        assert len(r.content.splitlines()) == len(SAMPLE) + 1


class TestKeyFiltering:
    def test_only_requested_keys_exported(self):
        r = export_env(SAMPLE, FORMAT_DOTENV, keys=["DB_HOST"])
        assert r.count == 1
        assert "DB_HOST" in r.keys
        assert "SECRET" not in r.keys

    def test_none_keys_exports_all(self):
        r = export_env(SAMPLE, FORMAT_DOTENV, keys=None)
        assert r.count == len(SAMPLE)

    def test_unknown_keys_silently_ignored(self):
        r = export_env(SAMPLE, FORMAT_DOTENV, keys=["DB_HOST", "DOES_NOT_EXIST"])
        assert r.count == 1


class TestUnsupportedFormat:
    def test_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            export_env(SAMPLE, "xml")

    def test_supported_formats_listed_in_error(self):
        with pytest.raises(ValueError) as exc_info:
            export_env(SAMPLE, "toml")
        for fmt in SUPPORTED_FORMATS:
            assert fmt in str(exc_info.value)
