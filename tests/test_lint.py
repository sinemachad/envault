"""Tests for envault.lint module."""

import pytest
from envault.lint import (
    lint_env,
    format_lint_results,
    LintResult,
    LintIssue,
)


class TestLintEmptyValues:
    def test_flags_empty_value(self):
        result = lint_env({"API_KEY": ""})
        codes = [i.code for i in result.issues]
        assert "W001" in codes

    def test_no_warning_for_nonempty_value(self):
        result = lint_env({"API_KEY": "abc"})
        codes = [i.code for i in result.issues]
        assert "W001" not in codes


class TestLintKeyNaming:
    def test_lowercase_key_triggers_w002(self):
        result = lint_env({"api_key": "value"})
        codes = [i.code for i in result.issues]
        assert "W002" in codes

    def test_uppercase_key_no_w002(self):
        result = lint_env({"API_KEY": "value"})
        codes = [i.code for i in result.issues]
        assert "W002" not in codes

    def test_underscore_prefix_triggers_i001(self):
        result = lint_env({"_INTERNAL": "value"})
        codes = [i.code for i in result.issues]
        assert "I001" in codes


class TestLintDuplicateKeys:
    def test_detects_duplicate(self):
        lines = ["API_KEY=abc\n", "API_KEY=xyz\n"]
        result = lint_env({"API_KEY": "xyz"}, raw_lines=lines)
        codes = [i.code for i in result.issues]
        assert "E001" in codes

    def test_no_error_for_unique_keys(self):
        lines = ["API_KEY=abc\n", "SECRET=xyz\n"]
        result = lint_env({"API_KEY": "abc", "SECRET": "xyz"}, raw_lines=lines)
        codes = [i.code for i in result.issues]
        assert "E001" not in codes

    def test_duplicate_issue_references_first_line(self):
        lines = ["API_KEY=abc\n", "API_KEY=xyz\n"]
        result = lint_env({"API_KEY": "xyz"}, raw_lines=lines)
        dup = next(i for i in result.issues if i.code == "E001")
        assert "line 1" in dup.message


class TestLintUnquotedSpaces:
    def test_detects_unquoted_space(self):
        lines = ["GREETING=hello world\n"]
        result = lint_env({"GREETING": "hello world"}, raw_lines=lines)
        codes = [i.code for i in result.issues]
        assert "W003" in codes

    def test_quoted_value_with_space_is_ok(self):
        lines = ['GREETING="hello world"\n']
        result = lint_env({"GREETING": "hello world"}, raw_lines=lines)
        codes = [i.code for i in result.issues]
        assert "W003" not in codes


class TestLintResult:
    def test_has_errors_true(self):
        r = LintResult(issues=[LintIssue(1, "K", "E001", "dup", "error")])
        assert r.has_errors is True

    def test_has_errors_false_for_warnings(self):
        r = LintResult(issues=[LintIssue(0, "K", "W001", "empty", "warning")])
        assert r.has_errors is False

    def test_has_warnings_true(self):
        r = LintResult(issues=[LintIssue(0, "K", "W001", "empty", "warning")])
        assert r.has_warnings is True


class TestFormatLintResults:
    def test_no_issues_message(self):
        result = LintResult()
        assert format_lint_results(result) == "No issues found."

    def test_format_contains_code(self):
        r = LintResult(issues=[LintIssue(3, "KEY", "W001", "empty value", "warning")])
        output = format_lint_results(r)
        assert "W001" in output
        assert "line 3" in output
