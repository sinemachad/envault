"""CLI commands for scope management."""

import sys

from envault.scope import add_scope, remove_scope, get_scope, list_scopes


def cmd_scope_add(args):
    try:
        entry = add_scope(
            args.base_dir,
            args.name,
            args.vault,
            description=args.description or "",
        )
    except (ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Scope '{entry['name']}' added -> {entry['vault']}")
    if entry.get("description"):
        print(f"  Description: {entry['description']}")


def cmd_scope_remove(args):
    try:
        remove_scope(args.base_dir, args.name)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Scope '{args.name}' removed.")


def cmd_scope_show(args):
    entry = get_scope(args.base_dir, args.name)
    if entry is None:
        print(f"Error: scope '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)
    print(f"name:        {entry['name']}")
    print(f"vault:       {entry['vault']}")
    print(f"description: {entry.get('description', '')}")


def cmd_scope_list(args):
    scopes = list_scopes(args.base_dir)
    if not scopes:
        print("No scopes registered.")
        return
    for s in scopes:
        desc = f"  # {s['description']}" if s.get("description") else ""
        print(f"{s['name']:20s} {s['vault']}{desc}")


def build_scope_subparsers(subparsers):
    scope_parser = subparsers.add_parser("scope", help="Manage environment scopes")
    scope_sub = scope_parser.add_subparsers(dest="scope_cmd")

    p_add = scope_sub.add_parser("add", help="Register a new scope")
    p_add.add_argument("name", help="Scope name")
    p_add.add_argument("vault", help="Path to vault file")
    p_add.add_argument("--description", default="", help="Optional description")
    p_add.add_argument("--base-dir", default=".", dest="base_dir")
    p_add.set_defaults(func=cmd_scope_add)

    p_rm = scope_sub.add_parser("remove", help="Remove a scope")
    p_rm.add_argument("name", help="Scope name")
    p_rm.add_argument("--base-dir", default=".", dest="base_dir")
    p_rm.set_defaults(func=cmd_scope_remove)

    p_show = scope_sub.add_parser("show", help="Show a scope")
    p_show.add_argument("name", help="Scope name")
    p_show.add_argument("--base-dir", default=".", dest="base_dir")
    p_show.set_defaults(func=cmd_scope_show)

    p_list = scope_sub.add_parser("list", help="List all scopes")
    p_list.add_argument("--base-dir", default=".", dest="base_dir")
    p_list.set_defaults(func=cmd_scope_list)

    return scope_parser
