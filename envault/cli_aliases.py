"""CLI commands for key aliasing."""

import argparse
import sys
from envault.aliases import add_alias, remove_alias, resolve_alias, list_aliases


def cmd_alias_add(args: argparse.Namespace) -> None:
    try:
        result = add_alias(args.alias, args.target, base_dir=args.dir)
        print(f"Alias '{result['alias']}' -> '{result['target']}' added.")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_alias_remove(args: argparse.Namespace) -> None:
    try:
        remove_alias(args.alias, base_dir=args.dir)
        print(f"Alias '{args.alias}' removed.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_alias_show(args: argparse.Namespace) -> None:
    target = resolve_alias(args.alias, base_dir=args.dir)
    if target is None:
        print(f"Alias '{args.alias}' not found.", file=sys.stderr)
        sys.exit(1)
    print(f"{args.alias} -> {target}")


def cmd_alias_list(args: argparse.Namespace) -> None:
    aliases = list_aliases(base_dir=args.dir)
    if not aliases:
        print("No aliases defined.")
        return
    width = max(len(a["alias"]) for a in aliases)
    for entry in aliases:
        print(f"{entry['alias']:<{width}}  ->  {entry['target']}")


def build_alias_subparsers(subparsers) -> None:  # noqa: ANN001
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dir", default=".", help="Base directory for alias store")

    p_add = subparsers.add_parser("alias-add", parents=[common], help="Add a key alias")
    p_add.add_argument("alias", help="Short alias name")
    p_add.add_argument("target", help="Full environment variable name")
    p_add.set_defaults(func=cmd_alias_add)

    p_rm = subparsers.add_parser("alias-remove", parents=[common], help="Remove a key alias")
    p_rm.add_argument("alias", help="Alias to remove")
    p_rm.set_defaults(func=cmd_alias_remove)

    p_show = subparsers.add_parser("alias-show", parents=[common], help="Resolve a single alias")
    p_show.add_argument("alias", help="Alias to resolve")
    p_show.set_defaults(func=cmd_alias_show)

    p_list = subparsers.add_parser("alias-list", parents=[common], help="List all aliases")
    p_list.set_defaults(func=cmd_alias_list)
