"""CLI commands for managing deprecated environment variable keys."""

import argparse
import sys

from envault.deprecations import (
    add_deprecation,
    check_env_deprecations,
    list_deprecations,
    remove_deprecation,
)
from envault.vault import unlock


def cmd_deprecation_add(args: argparse.Namespace) -> None:
    try:
        entry = add_deprecation(
            key=args.key,
            reason=args.reason,
            base_dir=args.base_dir,
            replacement=args.replacement,
            since=args.since,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Deprecated key '{entry.key}' recorded.")
    if entry.replacement:
        print(f"  Replacement : {entry.replacement}")
    if entry.since:
        print(f"  Since       : {entry.since}")
    print(f"  Reason      : {entry.reason}")


def cmd_deprecation_remove(args: argparse.Namespace) -> None:
    removed = remove_deprecation(key=args.key, base_dir=args.base_dir)
    if not removed:
        print(f"No deprecation entry found for '{args.key}'.", file=sys.stderr)
        sys.exit(1)
    print(f"Deprecation entry for '{args.key}' removed.")


def cmd_deprecation_list(args: argparse.Namespace) -> None:
    entries = list_deprecations(base_dir=args.base_dir)
    if not entries:
        print("No deprecated keys registered.")
        return
    for entry in entries:
        replacement = f" -> {entry.replacement}" if entry.replacement else ""
        since = f" (since {entry.since})" if entry.since else ""
        print(f"  {entry.key}{replacement}{since}: {entry.reason}")


def cmd_deprecation_check(args: argparse.Namespace) -> None:
    try:
        env = unlock(args.vault, args.key)
    except Exception as exc:
        print(f"Error unlocking vault: {exc}", file=sys.stderr)
        sys.exit(1)

    hits = check_env_deprecations(env, base_dir=args.base_dir)
    if not hits:
        print("No deprecated keys found in vault.")
        return

    print(f"Found {len(hits)} deprecated key(s):")
    for entry in hits:
        replacement = f" -> {entry.replacement}" if entry.replacement else ""
        print(f"  [DEPRECATED] {entry.key}{replacement}: {entry.reason}")
    sys.exit(2)


def build_deprecation_subparsers(sub: argparse._SubParsersAction) -> None:
    p_add = sub.add_parser("deprecation-add", help="Mark a key as deprecated")
    p_add.add_argument("key", help="Environment variable key")
    p_add.add_argument("reason", help="Reason for deprecation")
    p_add.add_argument("--replacement", default=None, help="Suggested replacement key")
    p_add.add_argument("--since", default=None, help="Version/date since deprecated")
    p_add.add_argument("--base-dir", default=".", help="Project base directory")
    p_add.set_defaults(func=cmd_deprecation_add)

    p_rm = sub.add_parser("deprecation-remove", help="Remove a deprecation entry")
    p_rm.add_argument("key", help="Environment variable key")
    p_rm.add_argument("--base-dir", default=".", help="Project base directory")
    p_rm.set_defaults(func=cmd_deprecation_remove)

    p_ls = sub.add_parser("deprecation-list", help="List all deprecated keys")
    p_ls.add_argument("--base-dir", default=".", help="Project base directory")
    p_ls.set_defaults(func=cmd_deprecation_list)

    p_chk = sub.add_parser("deprecation-check", help="Check vault for deprecated keys")
    p_chk.add_argument("vault", help="Path to encrypted vault file")
    p_chk.add_argument("key", help="Decryption key")
    p_chk.add_argument("--base-dir", default=".", help="Project base directory")
    p_chk.set_defaults(func=cmd_deprecation_check)
