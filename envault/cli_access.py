"""CLI commands for access control policies."""

from __future__ import annotations

import argparse
import sys

from envault.access import (
    set_allowed_keys,
    get_allowed_keys,
    remove_policy,
    list_policies,
)


def cmd_access_set(args: argparse.Namespace) -> None:
    """Set allowed keys for a profile."""
    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    if not keys:
        print("Error: --keys must be a non-empty comma-separated list.", file=sys.stderr)
        sys.exit(1)
    result = set_allowed_keys(args.base_dir, args.profile, keys)
    print(f"Access policy set for profile '{result['profile']}':")
    for k in result["allowed_keys"]:
        print(f"  {k}")


def cmd_access_remove(args: argparse.Namespace) -> None:
    """Remove access policy for a profile."""
    removed = remove_policy(args.base_dir, args.profile)
    if removed:
        print(f"Access policy removed for profile '{args.profile}'.")
    else:
        print(f"No access policy found for profile '{args.profile}'.")
        sys.exit(1)


def cmd_access_show(args: argparse.Namespace) -> None:
    """Show allowed keys for a profile."""
    keys = get_allowed_keys(args.base_dir, args.profile)
    if keys is None:
        print(f"No access policy set for '{args.profile}' (all keys allowed).")
    else:
        print(f"Profile '{args.profile}' may access:")
        for k in keys:
            print(f"  {k}")


def cmd_access_list(args: argparse.Namespace) -> None:
    """List all access policies."""
    policies = list_policies(args.base_dir)
    if not policies:
        print("No access policies defined.")
        return
    for profile, keys in sorted(policies.items()):
        print(f"{profile}: {', '.join(keys)}")


def build_access_subparsers(subparsers: argparse._SubParsersAction) -> None:
    access_parser = subparsers.add_parser("access", help="Manage key access policies")
    access_sub = access_parser.add_subparsers(dest="access_command")

    p_set = access_sub.add_parser("set", help="Set allowed keys for a profile")
    p_set.add_argument("profile", help="Profile name")
    p_set.add_argument("--keys", required=True, help="Comma-separated list of allowed env keys")
    p_set.add_argument("--base-dir", default=".", dest="base_dir")
    p_set.set_defaults(func=cmd_access_set)

    p_remove = access_sub.add_parser("remove", help="Remove access policy for a profile")
    p_remove.add_argument("profile", help="Profile name")
    p_remove.add_argument("--base-dir", default=".", dest="base_dir")
    p_remove.set_defaults(func=cmd_access_remove)

    p_show = access_sub.add_parser("show", help="Show allowed keys for a profile")
    p_show.add_argument("profile", help="Profile name")
    p_show.add_argument("--base-dir", default=".", dest="base_dir")
    p_show.set_defaults(func=cmd_access_show)

    p_list = access_sub.add_parser("list", help="List all access policies")
    p_list.add_argument("--base-dir", default=".", dest="base_dir")
    p_list.set_defaults(func=cmd_access_list)
