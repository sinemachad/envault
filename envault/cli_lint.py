"""CLI commands for envault lint."""

import argparse
import sys

from envault.vault import parse_env
from envault.lint import lint_env, format_lint_results


def cmd_lint(args: argparse.Namespace) -> None:
    """Lint a plain .env file for common issues."""
    try:
        with open(args.env_file, "r") as fh:
            raw_lines = fh.readlines()
        env = parse_env("".join(raw_lines))
    except FileNotFoundError:
        print(f"Error: file not found: {args.env_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Error reading env file: {exc}", file=sys.stderr)
        sys.exit(1)

    result = lint_env(env, raw_lines=raw_lines)
    output = format_lint_results(result)
    print(output)

    if result.has_errors:
        sys.exit(2)
    elif result.has_warnings and args.strict:
        sys.exit(2)


def build_lint_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register lint subcommands onto an existing subparser group."""
    parser_lint = subparsers.add_parser(
        "lint",
        help="Check a .env file for common issues.",
    )
    parser_lint.add_argument(
        "env_file",
        metavar="ENV_FILE",
        help="Path to the plain-text .env file to lint.",
    )
    parser_lint.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 2 on warnings as well as errors.",
    )
    parser_lint.set_defaults(func=cmd_lint)
