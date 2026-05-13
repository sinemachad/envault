"""CLI commands for vault quota management."""

from __future__ import annotations

import argparse
import sys

from envault.quota import (
    DEFAULT_QUOTA,
    check_quota,
    get_quota,
    remove_quota,
    set_quota,
)


def cmd_quota_set(args: argparse.Namespace) -> None:
    """Set the key limit for a vault."""
    try:
        entry = set_quota(args.base_dir, args.vault, args.limit)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(
        f"Quota set for '{entry.vault}': limit={entry.limit} keys."
    )


def cmd_quota_show(args: argparse.Namespace) -> None:
    """Show the quota for a vault."""
    entry = get_quota(args.base_dir, args.vault)
    status = "EXCEEDED" if entry.exceeded else "OK"
    print(
        f"Vault : {entry.vault}\n"
        f"Limit : {entry.limit}\n"
        f"Used  : {entry.current}\n"
        f"Free  : {entry.remaining}\n"
        f"Status: {status}"
    )


def cmd_quota_remove(args: argparse.Namespace) -> None:
    """Remove the quota setting for a vault (reverts to default)."""
    removed = remove_quota(args.base_dir, args.vault)
    if removed:
        print(
            f"Quota removed for '{args.vault}'. "
            f"Default limit ({DEFAULT_QUOTA}) now applies."
        )
    else:
        print(
            f"No quota record found for '{args.vault}'.",
            file=sys.stderr,
        )
        sys.exit(1)


def build_quota_subparsers(subparsers) -> None:  # type: ignore[type-arg]
    """Register quota sub-commands on *subparsers*."""
    quota_p = subparsers.add_parser("quota", help="Manage per-vault key quotas")
    quota_sub = quota_p.add_subparsers(dest="quota_cmd", required=True)

    # set
    p_set = quota_sub.add_parser("set", help="Set the key limit for a vault")
    p_set.add_argument("vault", help="Vault name or path")
    p_set.add_argument("limit", type=int, help="Maximum number of keys allowed")
    p_set.add_argument(
        "--base-dir", default=".", dest="base_dir",
        help="Directory containing .envault/ (default: .)"
    )
    p_set.set_defaults(func=cmd_quota_set)

    # show
    p_show = quota_sub.add_parser("show", help="Show quota info for a vault")
    p_show.add_argument("vault", help="Vault name or path")
    p_show.add_argument(
        "--base-dir", default=".", dest="base_dir",
        help="Directory containing .envault/ (default: .)"
    )
    p_show.set_defaults(func=cmd_quota_show)

    # remove
    p_rm = quota_sub.add_parser("remove", help="Remove quota setting for a vault")
    p_rm.add_argument("vault", help="Vault name or path")
    p_rm.add_argument(
        "--base-dir", default=".", dest="base_dir",
        help="Directory containing .envault/ (default: .)"
    )
    p_rm.set_defaults(func=cmd_quota_remove)
