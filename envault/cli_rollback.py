"""CLI commands for vault rollback."""

from __future__ import annotations

import argparse
import sys

from envault.rollback import list_rollback_points, rollback


def cmd_rollback_list(args: argparse.Namespace) -> None:
    points = list_rollback_points(args.vault)
    if not points:
        print("No rollback points available.")
        return
    print(f"{'#':<4}  {'Action':<30}  {'Timestamp'}")
    print("-" * 55)
    for i, entry in enumerate(points):
        print(f"{i:<4}  {entry['action']:<30}  {entry.get('timestamp', 'n/a')}")


def cmd_rollback(args: argparse.Namespace) -> None:
    try:
        result = rollback(args.vault, args.key, index=args.index)
    except (IndexError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(
            f"Rolled back '{result.vault_path}' to '{result.rolled_back_to}' "
            f"({result.keys_restored} keys restored)."
        )


def build_rollback_subparsers(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # envault rollback list
    p_list = sub.add_parser("rollback-list", help="List available rollback points")
    p_list.add_argument("vault", help="Path to encrypted vault file")
    p_list.set_defaults(func=cmd_rollback_list)

    # envault rollback
    p_rb = sub.add_parser("rollback", help="Restore vault to a previous state")
    p_rb.add_argument("vault", help="Path to encrypted vault file")
    p_rb.add_argument("key", help="Encryption key")
    p_rb.add_argument(
        "--index", type=int, default=0,
        help="Rollback point index (0 = most recent, default: 0)"
    )
    p_rb.add_argument("-q", "--quiet", action="store_true", help="Suppress output")
    p_rb.set_defaults(func=cmd_rollback)
