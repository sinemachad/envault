"""CLI commands for managing envault hooks."""

import argparse
import sys

from envault.hooks import VALID_EVENTS, add_hook, list_hooks, remove_hook


def cmd_hook_add(args: argparse.Namespace) -> None:
    try:
        result = add_hook(args.event, args.command, base_dir=args.dir)
        print(f"Hook registered: [{result['event']}] -> {result['command']}")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_hook_remove(args: argparse.Namespace) -> None:
    try:
        remove_hook(args.event, args.command, base_dir=args.dir)
        print(f"Hook removed: [{args.event}] -> {args.command}")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_hook_list(args: argparse.Namespace) -> None:
    hooks = list_hooks(base_dir=args.dir)
    if not hooks:
        print("No hooks registered.")
        return
    for event in VALID_EVENTS:
        cmds = hooks.get(event, [])
        if cmds:
            print(f"[{event}]")
            for cmd in cmds:
                print(f"  {cmd}")


def build_hooks_subparsers(subparsers) -> None:
    hooks_parser = subparsers.add_parser("hooks", help="Manage lifecycle hooks")
    hooks_sub = hooks_parser.add_subparsers(dest="hooks_cmd", required=True)

    # add
    p_add = hooks_sub.add_parser("add", help="Register a hook command for an event")
    p_add.add_argument("event", choices=VALID_EVENTS, help="Lifecycle event")
    p_add.add_argument("command", help="Shell command to run")
    p_add.add_argument("--dir", default=".", help="Base directory (default: .)")
    p_add.set_defaults(func=cmd_hook_add)

    # remove
    p_rm = hooks_sub.add_parser("remove", help="Remove a registered hook")
    p_rm.add_argument("event", choices=VALID_EVENTS, help="Lifecycle event")
    p_rm.add_argument("command", help="Shell command to remove")
    p_rm.add_argument("--dir", default=".", help="Base directory (default: .)")
    p_rm.set_defaults(func=cmd_hook_remove)

    # list
    p_ls = hooks_sub.add_parser("list", help="List all registered hooks")
    p_ls.add_argument("--dir", default=".", help="Base directory (default: .)")
    p_ls.set_defaults(func=cmd_hook_list)
