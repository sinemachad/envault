"""Lint .env files for common issues and best practices."""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class LintIssue:
    line: int
    key: str
    code: str
    message: str
    severity: str  # "error" | "warning" | "info"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)


def lint_env(env: Dict[str, str], raw_lines: List[str] = None) -> LintResult:
    """Run all lint checks against a parsed env dict and optional raw lines."""
    result = LintResult()
    result.issues.extend(_check_empty_values(env))
    result.issues.extend(_check_key_naming(env))
    result.issues.extend(_check_duplicate_keys(raw_lines or []))
    result.issues.extend(_check_unquoted_spaces(raw_lines or []))
    return result


def _check_empty_values(env: Dict[str, str]) -> List[LintIssue]:
    issues = []
    for key, value in env.items():
        if value == "":
            issues.append(LintIssue(
                line=0, key=key, code="W001",
                message=f"'{key}' has an empty value.",
                severity="warning"
            ))
    return issues


def _check_key_naming(env: Dict[str, str]) -> List[LintIssue]:
    issues = []
    for key in env:
        if not key.isupper():
            issues.append(LintIssue(
                line=0, key=key, code="W002",
                message=f"'{key}' should use UPPER_SNAKE_CASE.",
                severity="warning"
            ))
        if key.startswith("_"):
            issues.append(LintIssue(
                line=0, key=key, code="I001",
                message=f"'{key}' starts with underscore; may be internal.",
                severity="info"
            ))
    return issues


def _check_duplicate_keys(raw_lines: List[str]) -> List[LintIssue]:
    issues = []
    seen = {}
    for lineno, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in seen:
                issues.append(LintIssue(
                    line=lineno, key=key, code="E001",
                    message=f"'{key}' is defined more than once (first at line {seen[key]}).",
                    severity="error"
                ))
            else:
                seen[key] = lineno
    return issues


def _check_unquoted_spaces(raw_lines: List[str]) -> List[LintIssue]:
    issues = []
    for lineno, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        if value and not value.startswith(("'", '"')) and " " in value.split("#")[0].strip():
            issues.append(LintIssue(
                line=lineno, key=key.strip(), code="W003",
                message=f"'{key.strip()}' value contains spaces but is not quoted.",
                severity="warning"
            ))
    return issues


def format_lint_results(result: LintResult) -> str:
    if not result.issues:
        return "No issues found."
    lines = []
    for issue in sorted(result.issues, key=lambda i: (i.line, i.code)):
        prefix = {"error": "ERROR", "warning": "WARN ", "info": "INFO "}.get(issue.severity, "?????")
        loc = f"line {issue.line}" if issue.line else "     "
        lines.append(f"[{prefix}] {loc}  {issue.code}  {issue.message}")
    return "\n".join(lines)
