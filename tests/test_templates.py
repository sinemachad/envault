"""Tests for envault.templates."""

import json
import os
import pytest

from envault.templates import (
    load_template,
    generate_env_from_template,
    check_env_against_template,
)


SIMPLE_TEMPLATE = {
    "version": 1,
    "keys": [
        {"key": "DATABASE_URL", "description": "Postgres connection string", "required": True},
        {"key": "SECRET_KEY", "default": "changeme", "description": "App secret"},
        {"key": "DEBUG", "default": "false"},
    ],
}


@pytest.fixture
def template_file(tmp_path):
    path = tmp_path / "template.json"
    path.write_text(json.dumps(SIMPLE_TEMPLATE), encoding="utf-8")
    return str(path)


class TestLoadTemplate:
    def test_loads_valid_template(self, template_file):
        t = load_template(template_file)
        assert "keys" in t
        assert len(t["keys"]) == 3

    def test_raises_on_missing_keys_field(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text(json.dumps({"version": 1}), encoding="utf-8")
        with pytest.raises(ValueError, match="'keys' list"):
            load_template(str(p))

    def test_raises_on_entry_missing_key_field(self, tmp_path):
        p = tmp_path / "bad2.json"
        p.write_text(json.dumps({"keys": [{"default": "x"}]}), encoding="utf-8")
        with pytest.raises(ValueError, match="missing required field 'key'"):
            load_template(str(p))

    def test_raises_on_non_object_root(self, tmp_path):
        p = tmp_path / "bad3.json"
        p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with pytest.raises(ValueError, match="root must be a JSON object"):
            load_template(str(p))


class TestGenerateEnvFromTemplate:
    def test_generates_env_string(self):
        result = generate_env_from_template(SIMPLE_TEMPLATE)
        assert "DATABASE_URL=" in result
        assert "SECRET_KEY=changeme" in result
        assert "DEBUG=false" in result

    def test_includes_comments(self):
        result = generate_env_from_template(SIMPLE_TEMPLATE)
        assert "# Postgres connection string" in result
        assert "# App secret" in result

    def test_overrides_replace_defaults(self):
        result = generate_env_from_template(
            SIMPLE_TEMPLATE, overrides={"DEBUG": "true", "DATABASE_URL": "postgres://localhost/db"}
        )
        assert "DEBUG=true" in result
        assert "DATABASE_URL=postgres://localhost/db" in result

    def test_output_ends_with_newline(self):
        result = generate_env_from_template(SIMPLE_TEMPLATE)
        assert result.endswith("\n")


class TestCheckEnvAgainstTemplate:
    def test_detects_missing_required_keys(self):
        report = check_env_against_template(SIMPLE_TEMPLATE, {"SECRET_KEY": "x", "DEBUG": "false"})
        assert "DATABASE_URL" in report["missing"]

    def test_no_missing_when_all_required_present(self):
        report = check_env_against_template(
            SIMPLE_TEMPLATE,
            {"DATABASE_URL": "postgres://", "SECRET_KEY": "s", "DEBUG": "false"},
        )
        assert report["missing"] == []

    def test_detects_extra_keys(self):
        report = check_env_against_template(
            SIMPLE_TEMPLATE,
            {"DATABASE_URL": "postgres://", "UNKNOWN_VAR": "oops"},
        )
        assert "UNKNOWN_VAR" in report["extra"]

    def test_no_extra_when_all_keys_in_template(self):
        report = check_env_against_template(
            SIMPLE_TEMPLATE,
            {"DATABASE_URL": "postgres://", "SECRET_KEY": "s", "DEBUG": "true"},
        )
        assert report["extra"] == []
