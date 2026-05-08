"""Tests for envault.validate."""

import pytest
from envault.validate import (
    ValidationError,
    ValidationResult,
    validate_env,
    format_validation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_env():
    return {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "DEBUG": "true",
        "API_URL": "https://api.example.com",
        "ADMIN_EMAIL": "admin@example.com",
    }


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_valid_when_no_errors(self):
        r = ValidationResult()
        assert r.valid is True

    def test_invalid_when_errors_present(self):
        r = ValidationResult(errors=[ValidationError("KEY", "missing")])
        assert r.valid is False


# ---------------------------------------------------------------------------
# Required rule
# ---------------------------------------------------------------------------

class TestRequiredRule:
    def test_missing_required_key_raises_error(self):
        result = validate_env({}, [{"key": "SECRET", "required": True}])
        assert not result.valid
        assert result.errors[0].key == "SECRET"

    def test_empty_string_fails_required(self):
        result = validate_env({"SECRET": ""}, [{"key": "SECRET", "required": True}])
        assert not result.valid

    def test_present_value_passes_required(self, simple_env):
        result = validate_env(simple_env, [{"key": "APP_NAME", "required": True}])
        assert result.valid

    def test_missing_optional_key_is_ok(self):
        result = validate_env({}, [{"key": "OPTIONAL"}])
        assert result.valid


# ---------------------------------------------------------------------------
# Type rule
# ---------------------------------------------------------------------------

class TestTypeRule:
    def test_valid_int(self, simple_env):
        result = validate_env(simple_env, [{"key": "PORT", "type": "int"}])
        assert result.valid

    def test_invalid_int(self):
        result = validate_env({"PORT": "abc"}, [{"key": "PORT", "type": "int"}])
        assert not result.valid
        assert "int" in result.errors[0].message

    def test_valid_bool(self, simple_env):
        result = validate_env(simple_env, [{"key": "DEBUG", "type": "bool"}])
        assert result.valid

    def test_invalid_bool(self):
        result = validate_env({"DEBUG": "maybe"}, [{"key": "DEBUG", "type": "bool"}])
        assert not result.valid

    def test_valid_url(self, simple_env):
        result = validate_env(simple_env, [{"key": "API_URL", "type": "url"}])
        assert result.valid

    def test_invalid_url(self):
        result = validate_env({"API_URL": "not-a-url"}, [{"key": "API_URL", "type": "url"}])
        assert not result.valid

    def test_valid_email(self, simple_env):
        result = validate_env(simple_env, [{"key": "ADMIN_EMAIL", "type": "email"}])
        assert result.valid

    def test_invalid_email(self):
        result = validate_env({"ADMIN_EMAIL": "not-email"}, [{"key": "ADMIN_EMAIL", "type": "email"}])
        assert not result.valid

    def test_unknown_type_records_error(self):
        result = validate_env({"X": "val"}, [{"key": "X", "type": "uuid"}])
        assert not result.valid
        assert "Unknown type" in result.errors[0].message


# ---------------------------------------------------------------------------
# Pattern rule
# ---------------------------------------------------------------------------

class TestPatternRule:
    def test_matching_pattern_passes(self):
        result = validate_env({"CODE": "ABC-123"}, [{"key": "CODE", "pattern": r"[A-Z]+-\d+"}])
        assert result.valid

    def test_non_matching_pattern_fails(self):
        result = validate_env({"CODE": "abc"}, [{"key": "CODE", "pattern": r"[A-Z]+-\d+"}])
        assert not result.valid
        assert "pattern" in result.errors[0].message


# ---------------------------------------------------------------------------
# format_validation
# ---------------------------------------------------------------------------

class TestFormatValidation:
    def test_valid_result_message(self):
        r = ValidationResult()
        assert format_validation(r) == "All checks passed."

    def test_invalid_result_lists_errors(self):
        r = ValidationResult(errors=[ValidationError("KEY", "missing")])
        output = format_validation(r)
        assert "Validation failed" in output
        assert "KEY" in output
