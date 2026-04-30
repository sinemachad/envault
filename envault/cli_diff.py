"""CLI commands for diffing .env vault files."""

import argparse
import sys

from envault.vault import unlock
from envault.diff import diff_envs, format_diff


def cmd_diff(args: argparse.Namespace) -> None:
    """Decrypt two vault files and print the diff between them."""
    try:
        old_env = unlock(args.old_vault, args.key)
    except Exception as exc:
        print(f"Error decrypting {args.old_vault}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        new_env = unlock(args.new_vault, args.key)
    except Exception as exc:
        print(f"Error decrypting {args.new_vault}: {exc}", file=sys.stderr)
        sys.exit(1)

    mask = not args.show_values
    diff = diff_envs(old_env, new_env, mask_values=mask)

    if args.stat:
        print(f"Added:   {len(diff.added)}")
        print(f"Removed: {len(diff.removed)}")
        print(f"Changed: {len(diff.changed)}")
        print(f"Same:    {len(diff.unchanged)}")
        return

    print(format_diff(diff))

    if args.exit_code and diff.has_changes:
        sys.exit(1)


def build_diff_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'diff' subcommand."""
    parser = subparsers.add_parser(
        "diff",
        help="Show differences between two encrypted vault files",
    )
    parser.add_argument("old_vault", help="Path to the older vault file")
    parser.add_argument("new_vault", help="Path to the newer vault file")
    parser.add_argument(
        "--key",
        required=True,
        help="Shared encryption key",
    )
    parser.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Show plaintext values instead of masking them",
    )
    parser.add_argument(
        "--stat",
        action="store_true",
        default=False,
        help="Show summary counts only",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if there are differences",
    )
    parser.set_defaults(func=cmd_diff)
