"""Tests for envault.redact."""

import pytest

from envault.redact import (
    MASK,
    RedactResult,
    _key_is_sensitive,
    format_redacted,
    redact_env,
)


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "DB_PASSWORD": "s3cr3t",
    "API_TOKEN": "tok_abc123",
    "DEBUG": "true",
    "AWS_SECRET_KEY": "AKIAIOSFODNN7EXAMPLE",
}


class TestKeyIsSensitive:
    def test_password_suffix_detected(self):
        assert _key_is_sensitive("DB_PASSWORD", ["password"]) is True

    def test_non_sensitive_key(self):
        assert _key_is_sensitive("APP_NAME", ["password", "secret"]) is False

    def test_case_insensitive_match(self):
        assert _key_is_sensitive("My_Secret_Value", ["secret"]) is True


class TestRedactEnv:
    def test_returns_redact_result(self):
        result = redact_env(SAMPLE_ENV)
        assert isinstance(result, RedactResult)

    def test_sensitive_values_are_masked(self):
        result = redact_env(SAMPLE_ENV)
        assert result.redacted["DB_PASSWORD"] == MASK
        assert result.redacted["API_TOKEN"] == MASK
        assert result.redacted["AWS_SECRET_KEY"] == MASK

    def test_non_sensitive_values_unchanged(self):
        result = redact_env(SAMPLE_ENV)
        assert result.redacted["APP_NAME"] == "myapp"
        assert result.redacted["DEBUG"] == "true"

    def test_masked_keys_list_populated(self):
        result = redact_env(SAMPLE_ENV)
        assert "DB_PASSWORD" in result.masked_keys
        assert "API_TOKEN" in result.masked_keys
        assert "APP_NAME" not in result.masked_keys

    def test_original_env_unchanged(self):
        result = redact_env(SAMPLE_ENV)
        assert result.original["DB_PASSWORD"] == "s3cr3t"

    def test_extra_patterns_applied(self):
        env = {"STRIPE_PUBKEY": "pk_live_xxx", "NAME": "alice"}
        result = redact_env(env, extra_patterns=["pubkey"])
        assert result.redacted["STRIPE_PUBKEY"] == MASK
        assert result.redacted["NAME"] == "alice"

    def test_custom_keys_always_masked(self):
        env = {"TOTALLY_SAFE": "visible", "ALSO_SAFE": "also_visible"}
        result = redact_env(env, custom_keys=["TOTALLY_SAFE"])
        assert result.redacted["TOTALLY_SAFE"] == MASK
        assert result.redacted["ALSO_SAFE"] == "also_visible"

    def test_empty_env_returns_empty_result(self):
        result = redact_env({})
        assert result.redacted == {}
        assert result.masked_keys == []


class TestFormatRedacted:
    def test_returns_string(self):
        result = redact_env({"KEY": "val"})
        assert isinstance(format_redacted(result), str)

    def test_format_contains_key_equals_value(self):
        result = redact_env({"APP_NAME": "myapp"})
        assert "APP_NAME=myapp" in format_redacted(result)

    def test_sensitive_value_shown_as_mask(self):
        result = redact_env({"DB_PASSWORD": "secret"})
        assert f"DB_PASSWORD={MASK}" in format_redacted(result)
